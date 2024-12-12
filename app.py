import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile

# Function to download video
def download_video(url):
    temp_file = "downloaded_video.webm"
    try:
        subprocess.run(
            ['yt-dlp', '-f', 'best', '-o', temp_file, url],
            check=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")
        return temp_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video download: {e}")
        return None

# Function to validate video file
def validate_video_file(video_path):
    if not os.path.exists(video_path):
        st.error(f"Video file not found: {video_path}")
        return False
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            st.error("Failed to open video file. Ensure the file is valid.")
            return False
        cap.release()
        return True
    except Exception as e:
        st.error(f"Video validation failed: {e}")
        return False

# Function to extract frames
def extract_frames(video_path, output_folder, frame_rate=1):
    os.makedirs(output_folder, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frame_rate)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
        frame_count += 1

    cap.release()
    st.info(f"Frames extracted to: {output_folder}")

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

# Function to extract middle frames
def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    """
    Extracts one frame from the middle of each segment, given the total pages.
    """
    os.makedirs(output_folder, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps

    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    for i, timestamp in enumerate(segments):
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
            cv2.imwrite(frame_path, frame)

    cap.release()

# Function to create PDF
def create_pdf_from_frames(frame_folder, output_pdf):
    images = [
        Image.open(os.path.join(frame_folder, frame)).convert("RGB")
        for frame in sorted(os.listdir(frame_folder))
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
        if video_path and validate_video(video_path):
            frames_path = "frames"
            middle_frames_path = "middle_frames"
            output_pdf = "sheet_music_pages.pdf"

            # Step 1: Extract frames from the video
            extract_frames(video_path, frames_path, frame_rate=1)

            # Step 2: Determine total pages from extracted frames
            total_pages = extract_total_pages(frames_path)
            st.info(f"Total pages detected: {total_pages}")

            if total_pages > 0:
                # Step 3: Extract middle frames for each page
                extract_middle_frames(video_path, total_pages, middle_frames_path)

                # Step 4: Create a PDF from the extracted frames
                pdf_path = create_pdf_from_frames(middle_frames_path, output_pdf)
                if pdf_path:
                    # Step 5: Provide a download link for the PDF
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
            else:
                st.error("Failed to detect pages. Ensure the video contains visible sheet music.")
        else:
            st.error("Failed to process video. Ensure the video URL is valid.")
