import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile

# Function to download the video directly

def download_video(url):
    """
    Downloads the video in .webm format.
    """
    temp_file = NamedTemporaryFile(delete=False, suffix=".webm").name
    try:
        # Use yt-dlp to download the video in .webm format
        subprocess.run(
            ['yt-dlp', '-f', 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]', '-o', temp_file, url],
            check=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")
        return temp_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video download: {e}")
        return None

# Function to enhance images
def enhance_image(image_path):
    """
    Enhances the quality of an image by sharpening it.
    """
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    sharpening_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img, -1, sharpening_kernel)
    enhanced_path = image_path.replace(".jpg", "_enhanced.png")
    cv2.imwrite(enhanced_path, img_sharpened)
    return enhanced_path

# Function to create PDF
def create_pdf_from_frames(frame_folder, output_pdf):
    """
    Converts enhanced frames into a single PDF.
    """
    images = [
        Image.open(os.path.join(frame_folder, frame)).convert("RGB")
        for frame in sorted(os.listdir(frame_folder)) if frame.endswith("_enhanced.png")
    ]
    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        return output_pdf
    else:
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

# Function to segment video and extract middle frames
def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    """
    Extracts one frame from the middle of each segment, given the total pages.
    """
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    video_length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps

    # Exclude intro length and calculate segment duration
    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    # Extract frames at calculated timestamps
    for i, timestamp in enumerate(segments):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = vidcap.read()
        if success:
            frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Extracted frame for page {i + 1} at {timestamp:.2f}s")
            # Enhance the frame
            enhance_image(frame_path)

    vidcap.release()

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
