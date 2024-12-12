import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile

# Function to download the video
def download_video(url):
    temp_file = NamedTemporaryFile(delete=False, suffix=".webm").name
    try:
        # Use yt-dlp to download the video
        subprocess.run(
            ['yt-dlp', '-f', 'best', '-o', temp_file, url],
            check=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")
        return temp_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video download: {e}")
        return None

# Function to extract total pages
def extract_total_pages(frame_folder):
    """
    Scans frames to determine the total number of pages based on 'x/y' format.
    """
    total_pages = 0
    for frame in sorted(os.listdir(frame_folder)):
        frame_path = os.path.join(frame_folder, frame)
        img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
        text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")

        # Extract 'x/y' page number
        for line in text.splitlines():
            if "/" in line and line.strip().count("/") == 1:
                try:
                    _, pages = line.strip().split("/")
                    pages = int(pages)
                    total_pages = max(total_pages, pages)  # Update max pages
                except ValueError:
                    continue

    return total_pages

# Function to extract middle frames using MoviePy
def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    """
    Extracts one frame from the middle of each segment using MoviePy, given the total pages.
    """
    os.makedirs(output_folder, exist_ok=True)
    clip = VideoFileClip(video_path)
    video_length = clip.duration  # Get video length in seconds

    # Exclude intro length and calculate segment duration
    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    # Extract frames at calculated timestamps
    for i, timestamp in enumerate(segments):
        frame = clip.get_frame(timestamp)
        frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
        cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"Extracted frame for page {i + 1} at {timestamp:.2f}s")

    clip.close()

# Function to create PDF
def create_pdf_from_frames(frame_folder, output_pdf):
    """
    Converts enhanced frames into a single PDF.
    """
    images = [
        Image.open(os.path.join(frame_folder, frame)).convert("RGB")
        for frame in sorted(os.listdir(frame_folder)) if frame.endswith(".jpg")
    ]
    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        return output_pdf
    else:
        return None

# Streamlit UI
st.title("Drum Sheet Music Extractor")
video_url = st.text_input("Enter YouTube video URL:")

if st.button("Process Video"):
    with st.spinner("Downloading and processing video..."):
        video_path = download_video(video_url)
        if video_path:
            frames_path = "frames"
            middle_frames_path = "middle_frames"
            output_pdf = "sheet_music_pages.pdf"

            # Process video and generate PDF
            os.makedirs(frames_path, exist_ok=True)
            os.makedirs(middle_frames_path, exist_ok=True)
            total_pages = extract_total_pages(frames_path)
            extract_middle_frames(video_path, total_pages, middle_frames_path)
            pdf_path = create_pdf_from_frames(middle_frames_path, output_pdf)

            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f,
                        file_name="sheet_music_pages.pdf",
                        mime="application/pdf"
                    )
                st.success("PDF generated successfully!")
            else:
                st.error("Failed to generate PDF.")
