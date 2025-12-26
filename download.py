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
    return sid

def get_temp_dir(thread_number):
    temp_dir = f"thread_temp_{thread_number}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

def download_file_urllib(url, output_dir="."):
    try:
        with urllib.request.urlopen(url) as response:
            filename = None
            content_disposition = response.headers.get("Content-Disposition")
            
            if content_disposition:
                msg = EmailMessage() # use EmailMessage to get content_disposition https://peps.python.org/pep-0594/#cgi, https://stackoverflow.com/questions/8035900/how-to-get-filename-from-content-disposition-in-headers
                msg['content-disposition'] = content_disposition
                filename = msg.get_filename()

            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response, f)
                
            debug(f"Downloaded: {filepath}")
            return filepath
            
    except urllib.error.URLError as e:
        print(f"Error downloading {url}: {e}")

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
            try:
                date, lat, lon, media_type, download_url = line.strip().split(',', 4)

                sid = get_snapchat_media_id(download_url)
                if is_file_processed(sid):
                    print(f"    Already processed {sid}")
                    remove_dir(get_temp_dir(thread_number))
                    continue
                print(f"Processing: {sid}")
                debug(f"    Downloading {download_url}")
    
                downloaded_path = download_file_urllib(download_url, get_temp_dir(thread_number))
                print(f"    Downloaded to {downloaded_path}")
                
                determined_type = determine_media_type(downloaded_path)

                if determined_type == "ZIP":
                    merged_path = merge_files(unzip_file(downloaded_path, tempUnzipDir))
                    if merged_path.endswith(".mp4"):   
                        embed_mp4_location(merged_path, float(lat), float(lon))
                        embed_mp4_date(merged_path, date)
                    elif merged_path.endswith(".jpg") or merged_path.endswith(".jpeg"):
                        debug(f"            Date: {date} Lat: {lat} Lon: {lon}")
                        embed_jpg_date(merged_path, date)
                        embed_jpg_location(merged_path, float(lat), float(lon))

                    print(f"            Successfully processed ZIP: {download_url}")
                    
                elif determined_type in ["IMAGE", "VIDEO"]:
                    if determined_type == "VIDEO":
                        embed_mp4_date(downloaded_path, date)
                        embed_mp4_location(downloaded_path, float(lat), float(lon))
                    elif determined_type == "IMAGE":
                        debug(f"            Date: {date} Lat: {lat} Lon: {lon}")
                        embed_jpg_date(downloaded_path, date)
                        embed_jpg_location(downloaded_path, float(lat), float(lon))
                    print(f"            Successfully processed {determined_type}: {download_url}")
                
                mark_file_processed(sid)

                remove_dir(get_temp_dir(thread_number)) 
            except Exception as e:
                print(f"Error downloading media: {e}")
                print(f"Problematic line: {line.strip()}")   