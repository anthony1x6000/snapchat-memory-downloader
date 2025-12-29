import subprocess
import os

# Uses exiftool for metadata

def embed_mp4_location(video_path, lat, lon): # path, lat as float like 80.000, lon as float like -80.000 
    location_arg = f"{lat}, {lon}"

    try:
        cmd = [
            './exiftool',
            '-overwrite_original',
            f'-Keys:GPSCoordinates={location_arg}',
            f'-QuickTime:GPSCoordinates={location_arg}',
            f'-GPSCoordinates={location_arg}',
            f'-GPSPosition={location_arg}',
            video_path
        ] # Writing to as much as possible hoping one works, refer to https://exiftool.org/geotag.html
        
        # Execute exiftool command silently
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"                Location {location_arg} embedded in {video_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error: ExifTool returned {e.returncode}.")
    except FileNotFoundError:
        print("Error: 'exiftool' not found on system.")

def embed_mp4_date(video_path, date_string):
    try:
        cmd = [
            './exiftool',
            '-overwrite_original',
            f'-AllDates={date_string}',
            video_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"                Date {date_string} embedded in {video_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error: ExifTool returned {e.returncode}.")
    except FileNotFoundError:
        print("Error: 'exiftool' not found on system.")

# JPEG 

def embed_jpg_location(image_path, lat, lon):
    try:
        cmd = [
            './exiftool',
            '-overwrite_original',
            f'-GPSLatitude={lat}',
            f'-GPSLongitude={lon}',
            f'-GPSLatitudeRef={lat}',  
            f'-GPSLongitudeRef={lon}', 
            image_path
        ] # refer to https://exiftool.org/geotag.html
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"                Embedded coords {lat}, {lon} into {image_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to embed location. ExifTool returned {e.returncode}.")
    except FileNotFoundError:
        print("Error: 'exiftool' command not found. Please install ExifTool.")


def embed_jpg_date(image_path, date_string):
    try:
        cmd = [
            './exiftool',
            '-overwrite_original',
            f'-AllDates={date_string}', # https://exiftool.org/TagNames/Shortcuts.html
            image_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"                Embedded date {date_string} into {image_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to embed date. ExifTool returned {e.returncode}.")
    except FileNotFoundError:
        print("Error: 'exiftool' command not found. Please install ExifTool.")
