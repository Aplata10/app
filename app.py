import os
import streamlit as st
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageEnhance
import subprocess

# Streamlit UI
st.title("Drum Sheet Music Extractor")
st.markdown("""
Welcome **Drummer**! 🎶🥁

This app allows you to extract sheet music from drum tutorial videos and save it as a clean and clear PDF.
""")

# Input URL
video_url = st.text_input("Enter YouTube video URL:")
if st.button("Process Video"):
    with st.spinner("Downloading and processing video..."):
        try:
            # Step 1: Download MP4
            mp4_path = "downloaded_video.mp4"
            subprocess.run(
                ['yt-dlp', '-f', 'best[ext=mp4]', '-o', mp4_path, video_url],
                check=True
            )
            st.info(f"Video downloaded successfully: {mp4_path}")

            # Step 2: Extract Frames
            frames_path = "frames"
            os.makedirs(frames_path, exist_ok=True)
            vidcap = cv2.VideoCapture(mp4_path)
            fps = vidcap.get(cv2.CAP_PROP_FPS)
            total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

            st.info(f"Extracting {total_frames} frames...")
            for i in range(total_frames):
                success, frame = vidcap.read()
                if success:
                    frame_path = os.path.join(frames_path, f"frame_{i + 1}.jpg")
                    cv2.imwrite(frame_path, frame)

            vidcap.release()
            st.info(f"Frames extracted to: {frames_path}")

            # Step 3: Detect Total Pages
            def extract_total_pages(frame_folder):
                total_pages = 0
                for frame in sorted(os.listdir(frame_folder)):
                    frame_path = os.path.join(frame_folder, frame)
                    img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
                    text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
                    st.text(f"Detected text in {frame}: {text}")  # Debugging
                    for line in text.splitlines():
                        if "/" in line and line.strip().count("/") == 1:
                            try:
                                _, pages = line.strip().split("/")
                                pages = int(pages)
                                total_pages = max(total_pages, pages)
                            except ValueError:
                                continue
                return total_pages

            total_pages = extract_total_pages(frames_path)
            if total_pages == 0:
                st.warning("No pages detected. Ensure the video contains visible sheet music.")
            else:
                st.success(f"Total pages detected: {total_pages}")

                # Step 4: Generate PDF
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

                output_pdf = "sheet_music_pages.pdf"
                pdf_path = create_pdf_from_frames(frames_path, output_pdf)
                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f,
                            file_name="sheet_music_pages.pdf",
                            mime="application/pdf"
                        )
        except Exception as e:
            st.error(f"Error: {e}")
