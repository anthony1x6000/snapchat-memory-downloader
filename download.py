import shutil
import sys
import urllib.request
import urllib.parse
from urllib.parse import urlparse, parse_qs
import os
from email.message import EmailMessage

import sqlite3

from process import *
from metadata import *
from main import remove_dir

DATABASE = "processed_files.db"
TIMEOUT_SECONDS = 30

def init_db(): 
    with sqlite3.connect(DATABASE, timeout=TIMEOUT_SECONDS) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS processed_files (filename TEXT PRIMARY KEY)")

def is_file_processed(filename):
    with sqlite3.connect(DATABASE, timeout=TIMEOUT_SECONDS) as conn:
        cursor = conn.execute("SELECT 1 FROM processed_files WHERE filename=?", (filename,))
        return cursor.fetchone() is not None
    
def mark_file_processed(filename):
    with sqlite3.connect(DATABASE, timeout=TIMEOUT_SECONDS) as conn:
        conn.execute("INSERT OR IGNORE INTO processed_files (filename) VALUES (?)", (filename,))

def get_snapchat_media_id(download_url):
    parsed_url = urlparse(download_url)
    query_params = parse_qs(parsed_url.query)
    sid = query_params.get('sid', [''])[0]
    if not sid:
        import hashlib
        sid = hashlib.md5(download_url.encode('utf-8')).hexdigest()
    return sid

def get_temp_dir(thread_number):
    temp_dir = f"thread_temp_{thread_number}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

def get_others_dir():
    others_dir = "others"
    if not os.path.exists(others_dir):
        os.makedirs(others_dir, exist_ok=True)
    return others_dir

def download_file_urllib(url, output_dir="."):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            filename = None
            content_disposition = response.headers.get("Content-Disposition")
            
            if content_disposition:
                try:
                    msg = EmailMessage()
                    msg['content-disposition'] = content_disposition
                    filename = msg.get_filename()
                except Exception:
                    pass

            # Fallback 1: Extract from URL path
            if not filename:
                parsed_url = urlparse(url)
                path_filename = os.path.basename(parsed_url.path)
                if path_filename:
                    filename = urllib.parse.unquote(path_filename)

            # Fallback 2: Generate based on URL hash
            if not filename:
                sid = get_snapchat_media_id(url)
                filename = f"media_{sid}"

            # Ensure we don't have directory traversal or illegal characters in filename
            filename = os.path.basename(filename)

            # If filename doesn't have an extension, try to determine it from Content-Type
            name, ext = os.path.splitext(filename)
            if not ext:
                content_type = response.headers.get("Content-Type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    filename += ".jpg"
                elif "png" in content_type:
                    filename += ".png"
                elif "mp4" in content_type:
                    filename += ".mp4"
                elif "zip" in content_type:
                    filename += ".zip"
                elif "quicktime" in content_type or "mov" in content_type:
                    filename += ".mov"
                elif "gif" in content_type:
                    filename += ".gif"
                elif "audio" in content_type:
                    filename += ".m4a"

            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response, f)
                
            debug(f"Downloaded: {filepath}")
            return filepath
            
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download.py <csv>")
        sys.exit(1)

    init_db() # Create database 
    
    thread_number = sys.argv[1].replace("data/thread_", "").replace(".csv", "")
    tempUnzipDir = os.path.join(get_temp_dir(thread_number), "unzipped")
    filepath = sys.argv[1]
    debug(f"Processing file: {filepath}")

    # CSV in format Date,Latitude,Longitude,Media Type,Download Url
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f)  # Skip header line
        for line in f:
            downloaded_path = None
            sid = None
            try:
                line_parts = line.strip().split(',', 4)
                if len(line_parts) < 5:
                    print(f"Skipping malformed CSV line: {line.strip()}")
                    continue
                date, lat, lon, media_type, download_url = line_parts
                if not download_url:
                    print(f"Skipping empty download URL: {line.strip()}")
                    continue

                sid = get_snapchat_media_id(download_url)
                if is_file_processed(sid):
                    print(f"    Already processed {sid}")
                    remove_dir(get_temp_dir(thread_number))
                    continue
                print(f"Processing: {sid}")
                debug(f"    Downloading {download_url}")
    
                downloaded_path = download_file_urllib(download_url, get_temp_dir(thread_number))
                if not downloaded_path or not os.path.exists(downloaded_path):
                    print(f"    Failed to download {download_url}")
                    continue

                print(f"    Downloaded to {downloaded_path}")
                
                try:
                    determined_type = determine_media_type(downloaded_path)
                    debug(f"            Date: {date} Lat: {lat} Lon: {lon}")

                    processed = False
                    if determined_type == "ZIP":
                        unzipped_files = unzip_file(downloaded_path, tempUnzipDir)
                        merged_path = merge_files(unzipped_files)
                        if merged_path:
                            if merged_path.endswith(".mp4"):   
                                embed_mp4_location(merged_path, float(lat), float(lon))
                                embed_mp4_date(merged_path, date)
                                set_modification_date(merged_path)
                                processed = True
                            elif merged_path.endswith(".jpg") or merged_path.endswith(".jpeg"):
                                embed_jpg_date(merged_path, date)
                                embed_jpg_location(merged_path, float(lat), float(lon))
                                set_modification_date(merged_path)
                                processed = True
                        
                        if processed:
                            print(f"            Successfully processed ZIP: {download_url}")
                        else:
                            raise ValueError("ZIP did not contain a mergeable image or video")
                        
                    elif determined_type in ["IMAGE", "VIDEO"]:
                        if determined_type == "VIDEO":
                            embed_mp4_date(downloaded_path, date)
                            embed_mp4_location(downloaded_path, float(lat), float(lon))
                            set_modification_date(downloaded_path)
                        elif determined_type == "IMAGE":
                            embed_jpg_date(downloaded_path, date)
                            embed_jpg_location(downloaded_path, float(lat), float(lon))
                            set_modification_date(downloaded_path)
                        
                        final_path = os.path.join(get_output_dir(), os.path.basename(downloaded_path))
                        shutil.move(downloaded_path, final_path) # move to output

                        print(f"            Successfully processed {determined_type}: {download_url}")
                        processed = True

                    else:
                        raise ValueError(f"Unexpected media type: {determined_type}")

                except Exception as proc_err:
                    # Save the original downloaded file to others/
                    others_dir = get_others_dir()
                    filename = os.path.basename(downloaded_path)
                    others_path = os.path.join(others_dir, filename)
                    shutil.move(downloaded_path, others_path)
                    print(f"            Processing issue ({proc_err}). Saved original downloaded file to {others_path}")

                mark_file_processed(sid)
                remove_dir(get_temp_dir(thread_number)) 
            except Exception as e:
                print(f"Error downloading media: {e}")
                print(f"Problematic line: {line.strip()}")   