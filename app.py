import os
import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import subprocess
import easyocr

st.title("Drum Sheet Music Extractor")
st.markdown("""
Welcome **Drummer**! 🎶🥁

This app allows you to extract sheet music from drum tutorial videos and save it as a clean and clear PDF.
It's designed to work best with YouTube shorts that display drum sheet music on the screen.
""")

# Input for video URL
video_url = st.text_input("Enter YouTube video URL:")

if st.button("Process Video"):
    with st.spinner("Downloading and processing video..."):
        # Download video as MP4
        mp4_path = download_video_as_mp4(video_url)
        if mp4_path:
            frames_path = "frames"
            output_pdf = "sheet_music_pages.pdf"

            # Clear previous frames
            if os.path.exists(frames_path):
                for file in os.listdir(frames_path):
                    os.remove(os.path.join(frames_path, file))
            os.makedirs(frames_path, exist_ok=True)

            # Extract frames and process
            st.info("Extracting frames...")
            total_pages = extract_total_pages(frames_path)
            if total_pages > 0:
                extract_frames(mp4_path, frames_path, total_pages)
                pdf_path = create_pdf_from_frames(frames_path, output_pdf)

                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f,
                            file_name="sheet_music_pages.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error("Failed to generate PDF.")
            else:
                st.error("No pages detected. Ensure the video contains visible sheet music.")

st.header("Instructions")
st.markdown("""
1. Paste the link to a YouTube short containing sheet music.
2. Click **Process Video** and wait for the app to process the video.
3. Download your extracted file as a PDF.

### Recommended Video Types:
- Videos that show clear, static drum sheet music on-screen.
- Videos without excessive animations or overlays.
- Clearly marked page numbers

### Suggested Channel:
    @SightReadDrums

Below is an example of a recommended video:
""")
st.image("example1.png", caption="Example #1", use_container_width=True)
st.image("example2.png", caption="Example #2", use_container_width=True)

# Function to download the video in MP4 format
def download_video_as_mp4(url, output_file="downloaded_video.mp4"):
    try:
        subprocess.run(
            ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_file, url],
            check=True
        )
        if os.path.exists(output_file):
            st.info(f"Video downloaded successfully: {output_file}")
            return output_file
        else:
            st.error("Failed to download the video.")
            return None
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video download: {e}")
        return None

# Function to enhance images
def enhance_image(image):
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    enhancer = ImageEnhance.Sharpness(pil_image)
    enhanced_image = enhancer.enhance(2.0)  # Increase sharpness
    return cv2.cvtColor(np.array(enhanced_image), cv2.COLOR_RGB2BGR)

# Function to create PDF
def create_pdf_from_frames(frame_folder, output_pdf):
    images = [
        Image.open(os.path.join(frame_folder, frame)).convert("RGB")
        for frame in sorted(os.listdir(frame_folder)) if frame.endswith(".jpg")
    ]
    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        st.success(f"PDF generated: {output_pdf}")
        return output_pdf
    else:
        st.error("No frames to include in PDF.")
        return None

# Function to extract frames
def extract_frames(video_path, output_folder, total_pages, intro_length=5):
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        st.error("Invalid video FPS. Ensure the video file is correct.")
        return
    video_length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps

    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    for i, timestamp in enumerate(segments):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = vidcap.read()
        if success:
            enhanced_frame = enhance_image(frame)
            frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
            cv2.imwrite(frame_path, enhanced_frame)
            st.info(f"Frame for page {i + 1} extracted at {timestamp:.2f}s.")
        else:
            st.warning(f"Failed to extract frame for page {i + 1}.")
    vidcap.release()

# Function to extract total pages using EasyOCR
def extract_total_pages(frame_folder):
    reader = easyocr.Reader(['en'])  # Load EasyOCR
    total_pages = 0
    for frame in sorted(os.listdir(frame_folder)):
        frame_path = os.path.join(frame_folder, frame)
        text = reader.readtext(frame_path, detail=0)  # Extract text from image
        for line in text:
            if "/" in line and line.strip().count("/") == 1:
                try:
                    _, pages = line.strip().split("/")
                    pages = int(pages)
                    total_pages = max(total_pages, pages)
                except ValueError:
                    continue
    return total_pages
