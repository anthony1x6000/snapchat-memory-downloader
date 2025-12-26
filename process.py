from PIL import Image
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
import os
from download import get_temp_dir
from main import debug

def get_output_dir():
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def process_image(base_path, overlay_path, output_path): # Apply overlay to image
    debug(f"        Output: {output_path}")
    debug(f"        Overlay: {overlay_path}")
    debug(f"        Base: {base_path}")

    save_path = os.path.join(output_path, os.path.basename(base_path))

    try:
        with Image.open(base_path).convert("RGBA") as base:
            with Image.open(overlay_path).convert("RGBA") as overlay:
                overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)
                base.paste(overlay, (0, 0), overlay)
                base.convert("RGB").save(save_path)
    except Exception as e:
        print(f"Error processing image: {e}")
        return -1
    return save_path

def process_video(base_path, overlay_path, output_path): # Apply overlay to video 
    debug(f"        Output: {output_path}")
    debug(f"        Overlay: {overlay_path}")
    debug(f"        Base: {base_path}")

    save_path = os.path.join(output_path, os.path.basename(base_path))

    try:
        video_clip = VideoFileClip(base_path)
        overlay_clip = (ImageClip(overlay_path)
                        .with_duration(video_clip.duration)
                        .resized(new_size=video_clip.size)
                        .with_position(('center', 'center')))
        
        final_clip = CompositeVideoClip([video_clip, overlay_clip])
        
        temp_audio = f"temp-audio-{os.getpid()}.m4a" # AI said this will prevent multithreaded crashes

        print("\nSTART MOVIEPY:")        
        final_clip.write_videofile(save_path, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio)

        video_clip.close()
        final_clip.close()
        
        # Cleanup unique audio temp file
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    except Exception as e:
        print(f"Error processing video: {e}")
        return -1
    return save_path

def merge_files(list):
    overlay, base_video, base_image = 0, 0, 0
    for file in list:
        if file.endswith(".png"):
            overlay = file
        elif file.endswith(".jpg") or file.endswith(".jpeg"):
            base_image = file
        elif file.endswith(".mp4"):
            base_video = file
    if base_video != 0: 
        return process_video(base_video, overlay, get_output_dir())
    elif base_image != 0:
        return process_image(base_image, overlay, get_output_dir())

def unzip_file(zip_path, extract_to):
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return [os.path.join(extract_to, f) for f in os.listdir(extract_to)]

def determine_media_type(filename):
    if filename.lower().endswith((".jpg", ".jpeg")):
        return 'IMAGE'
    elif filename.lower().endswith(".mp4"):
        return 'VIDEO'
    elif filename.lower().endswith(".zip"):
        return 'ZIP'
    else:
        return 'Unknown'
    
def determine_media_in_unzipped_dir(directory):
    for file in os.listdir(directory):
        determine_media_type(file)