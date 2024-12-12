import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile
from imageio.v3 import imread
import shutil
# Function to download video
def download_video(url):
    temp_file = NamedTemporaryFile(delete=False, suffix=".webm").name
    output_file = "downloaded_video.webm"
    try:
        # Use yt-dlp to download the video
        subprocess.run(
            ['yt-dlp', '-f', 'best', '-o', temp_file, url],
            check=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")

        # Copy the file to the desired location
        shutil.copyfile(temp_file, output_file)

        # Remove the temporary file
        os.remove(temp_file)

        return output_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video download: {e}")
        return None

# Function to enhance images
def enhance_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    sharpening_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img, -1, sharpening_kernel)
    enhanced_path = image_path.replace(".jpg", "_enhanced.png")
    cv2.imwrite(enhanced_path, img_sharpened)
    return enhanced_path

# Function to extract total pages
# Function to extract total pages
def extract_total_pages(frame_folder):
    """
    Scans frames to determine the total number of pages based on 'x/y' format.
    """
    total_pages = 0
    print("Starting page detection...")
    for frame in sorted(os.listdir(frame_folder)):
        frame_path = os.path.join(frame_folder, frame)
        img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
        text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
        
        # Log extracted text for debugging
        print(f"Frame: {frame}, Extracted Text:\n{text}\n{'-'*50}")

        # Extract 'x/y' page number
        for line in text.splitlines():
            if "/" in line and line.strip().count("/") == 1:
                try:
                    _, pages = line.strip().split("/")
                    pages = int(pages)
                    total_pages = max(total_pages, pages)  # Update max pages
                except ValueError:
                    continue

    print(f"Detected total pages: {total_pages}")
    return total_pages

# Function to extract frames
# Function to extract frames from video
def extract_frames(video_path, frame_folder, frame_rate=1):
    """
    Extracts frames from a video at the specified frame rate.
    """
    os.makedirs(frame_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)

    if not vidcap.isOpened():
        print("Failed to open video file.")
        return

    print(f"Video FPS: {fps}")
    interval = int(fps / frame_rate)  # Calculate interval between frames

    success, frame = vidcap.read()
    count = 0
    total_frames = 0

    while success:
        if count % interval == 0:
            frame_path = os.path.join(frame_folder, f"frame_{count}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Saved frame at {frame_path}")
            total_frames += 1
        success, frame = vidcap.read()
        count += 1

    vidcap.release()
    print(f"Total frames extracted: {total_frames}")

# Function to extract middle frames
def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    video_length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
    segment_duration = (video_length - intro_length) / total_pages
    segments = [intro_length + segment_duration * i + segment_duration / 2 for i in range(total_pages)]

    for i, timestamp in enumerate(segments):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = vidcap.read()
        if success:
            frame_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
            cv2.imwrite(frame_path, frame)
            enhance_image(frame_path)
    vidcap.release()

# Function to create PDF
def create_pdf_from_frames(frame_folder, output_pdf):
    images = [
        Image.open(os.path.join(frame_folder, frame)).convert("RGB")
        for frame in sorted(os.listdir(frame_folder)) if frame.endswith("_enhanced.png")
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
