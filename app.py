import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile

def download_video(url):
    temp_file = NamedTemporaryFile(delete=False, suffix=".webm").name
    output_file = "downloaded_video.mp4"
    try:
        # Use yt-dlp to download the video
        subprocess.run(
            ['yt-dlp', '-f', 'best', '-o', temp_file, url],
            check=True,
            text=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")

        # Convert the video to MP4 format using ffmpeg
        subprocess.run(
            ['ffmpeg', '-i', temp_file, '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', output_file],
            check=True,
            text=True
        )
        st.info(f"Video converted to MP4 format as {output_file}")

        # Remove the temporary file
        os.remove(temp_file)

        return output_file
    except subprocess.CalledProcessError as e:
        st.error(f"Error during video processing: {e}")
        return None
    except FileNotFoundError as e:
        st.error(f"Required executable not found: {e}")
        return None

def enhance_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    sharpening_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img, -1, sharpening_kernel)
    enhanced_path = image_path.replace(".jpg", "_enhanced.png")
    cv2.imwrite(enhanced_path, img_sharpened)
    return enhanced_path

def extract_total_pages(frame_folder):
    total_pages = 0
    for frame in sorted(os.listdir(frame_folder)):
        frame_path = os.path.join(frame_folder, frame)
        img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
        text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
        for line in text.splitlines():
            if "/" in line and line.strip().count("/") == 1:
                try:
                    _, pages = line.strip().split("/")
                    pages = int(pages)
                    total_pages = max(total_pages, pages)
                except ValueError:
                    continue
    return total_pages

def extract_middle_frames(video_path, total_pages, output_folder, intro_length=5):
    os.makedirs(output_folder, exist_ok=True)
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    video_length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps

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

st.title("Drum Sheet Music Extractor")
video_url = st.text_input("Enter YouTube video URL:")

if st.button("Process Video"):
    with st.spinner("Downloading and processing video..."):
        video_path = download_video(video_url)
        if video_path:
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
                st.error("No valid pages detected in video frames.")

