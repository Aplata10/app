import os
import cv2
import pytesseract
from PIL import Image
import streamlit as st
import numpy as np

# Function to validate video file
def validate_video(video_path):
    vidcap = cv2.VideoCapture(video_path)
    if not vidcap.isOpened():
        st.error("Failed to open video file. Ensure the file is valid.")
        return False
    return True

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

# Function to extract middle frames from video
def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    """
    Extracts one frame from the middle of each segment, given the total pages.
    """
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)

    fps = vidcap.get(cv2.CAP_PROP_FPS)
    total_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_length = total_frames / fps

    if not fps or not total_frames:
        st.error("Failed to read video metadata. Ensure the video file is valid.")
        return

    # Exclude intro length and calculate segment duration
    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    # Extract frames at calculated timestamps
    for i, timestamp in enumerate(segments):
        frame_number = int(timestamp * fps)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = vidcap.read()
        if success:
            frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Extracted frame for page {i + 1} at {timestamp:.2f}s")
        else:
            print(f"Failed to extract frame for page {i + 1}")

    vidcap.release()

# Function to create PDF from frames
def create_pdf_from_frames(frame_folder, output_pdf):
    """
    Converts frames into a single PDF.
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
    with st.spinner("Processing video..."):
        video_path = "downloaded_video.webm"  # Replace with actual path if downloaded dynamically
        if validate_video(video_path):
            frames_path = "frames"
            middle_frames_path = "middle_frames"
            output_pdf = "sheet_music_pages.pdf"

            os.makedirs(frames_path, exist_ok=True)
            os.makedirs(middle_frames_path, exist_ok=True)

            total_pages = extract_total_pages(frames_path)
            if total_pages > 0:
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
            else:
                st.error("Failed to determine total pages.")
