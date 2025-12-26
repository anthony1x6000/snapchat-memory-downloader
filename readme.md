# Snapchat Memory Downloader 

These scripts:
- Download your snapchat memories from `memories_history.json`
- Apply the overlay, so applicable snaps still have text and stickers
- Embed location and date metadata. 
- Embed quicktime location and date metadata to videos (for better apple support)
- Export all to an output directory. 

## Usage

`python3 main.py memories_history.json <threads>`

## Works on
The metadata stuff is a bit iffy, since I don't have access to any macOS device. \
- The metadata is properly embedded and viewable on Ubuntu 2404.
- When images are saved to gallery via a web browser (e.g. upload a memory to a file hosting site, downloading that to iOS device) location and date metadata are properly stored.
- When videos are saved to gallery via a cloud hosting service such as Filen, the location and date metadata are properly stored. 
Outside of those above three cases, metadata is not properly accessible on iOS devices. \
**I will have to test on a macOS device when I get a hold of one, so images and videos can be uploaded to iCloud or moved directly onto an iPhone**

## A little more in depth explination 

Input your `memories_history.json`, the number of threads (concurrent downloads and video/image processing), and this will:
- Download the video, image, or zip. 
- In the case of a zip:
    - Extract the zip
        - The zip will contain: 
            - PNG overlay 
            - JPG or MP4
    - `process.py` will then use PIL or moviepy to overlay the overlay (PNG) over the base media (MP4 or JPG)
- If there is no zip, and a video or image is downloaded, this means there is no overlay.
- After adding the overlay, if applicable:
    - `metadata.py` is used to add the date and lat, lon coordinates (location) to the metadata of the image or video. 
- The script is done. 