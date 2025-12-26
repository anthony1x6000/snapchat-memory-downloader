import json
import sys
import os
import subprocess  # Added for process management

DEBUG = False

def debug(string):
    if DEBUG:
        print(string)

def remove_dir(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)

def get_media_subset(media_list, num_threads): # Round Robin Distribution
    chunks = [[] for _ in range(num_threads)] # Generate empty lists for in range of num_threads like [ [], [], [] ]
    for index, item in enumerate(media_list):  # Walk every item in media_list with its position in the original list (index)
        target_bucket = index % num_threads  # Determine which chunk to put the media in (0 to num_threads-1)
        chunks[target_bucket].append(item)  # Append item to chunk 

    return [c for c in chunks if c] # Return only non-empty chunks

def push_media_to_thread_file(media_subset, thread_data, thread_index):
    os.makedirs(thread_data, exist_ok=True)
    thread_csv_file_path = os.path.join(thread_data, f"thread_{thread_index}.csv") 

    with open(thread_csv_file_path, 'w', encoding='utf-8') as f:
        f.write("Date,Latitude,Longitude,Media Type,Download Url\n") # CSV Header
        
        for media in media_subset: # Walk the subset of media 
            try:
                date = media.get("Date", "") #e.g       "Date": "2025-12-24 21:38:33 UTC",
                location = media.get("Location", "") # e.g.       "Location": "Latitude, Longitude: 43.412506, -80.46055",
                if "Latitude, Longitude: " in location:
                    lat, lon = location.split(": ")[1].split(", ") # pulls 43.412506, -80.46055 from "Latitude, Longitude: 43.412506, -80.46055"
                else:
                    lat, lon = "0.0", "0.0" 

                media_type = media.get("Media Type", "") # e.g       "Media Type": "Video",
                download_url = media.get("Media Download Url", "") # e.g.       "Media Download Url": "URL"
                
                f.write(f"{date},{lat},{lon},{media_type},{download_url}\n")
            except Exception as e:
                print(f"Skipping error item: {e}")

def run_downloaders(num_threads, output_dir):
    processes = []

    try:
        for i in range(num_threads): # For each thread
            csv_path = os.path.join(output_dir, f"thread_{i}.csv")
            
            if not os.path.exists(csv_path):
                continue # Skip if file doesn't exist

            cmd = [sys.executable, "download.py", csv_path] # run python3 download.py thread_data/thread_n.csv
            
            p = subprocess.Popen(cmd) # Start the process in background (via Popen)
            processes.append(p) # add process to list 
                
        for p in processes:
            p.wait() # Wait for each process to finish
            
    except KeyboardInterrupt: # if ctrl + c
        for p in processes: 
            if p.poll() is None: 
                p.terminate() 
                # p.kill() # pkill 
                print(f"Terminated {p.pid}")
        print("Stopped all threads")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <memories_history.json (or another JSON file)> <number_of_threads>")
        sys.exit(1)

    file_path = sys.argv[1]
    num_threads = int(sys.argv[2])
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    media_list = data.get("Saved Media", [])
    chunks = get_media_subset(media_list, num_threads)
    thread_data = "thread_data"

    for i, chunk in enumerate(chunks):
        push_media_to_thread_file(chunk, thread_data, i)
        if DEBUG: print(f"Thread {i}: wrote {len(chunk)} items to {thread_data}/thread_{i}.csv")

    if chunks:
        run_downloaders(len(chunks), thread_data) # Start each thread
    else:
        print("No media found to process.")

    remove_dir(thread_data)
    # Clean up temporary audio files
    for file in os.listdir('.'):
        if file.startswith('temp-audio-') and file.endswith('.m4a'):
            try:
                os.remove(file)
            except OSError:
                pass

    print("Done.")
