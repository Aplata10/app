import os
import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np
import ffmpeg
from tempfile import NamedTemporaryFile

# Function to download and convert video
def download_video(url):
    temp_file = NamedTemporaryFile(delete=False, suffix=".webm").name
    output_file = "downloaded_video.mp4"
    try:
        # Use yt-dlp to download the video
        subprocess.run(
            ['yt-dlp', '-f', 'best', '-o', temp_file, url],
            check=True
        )
        st.info(f"Video downloaded successfully as {temp_file}")

        # Use ffmpeg-python to convert the video
        ffmpeg.input(temp_file).output(output_file, vcodec="libx264", acodec="aac", preset="fast", crf=20, pix_fmt="yuv420p").run(overwrite_output=True)
        st.info(f"Video converted to MP4 format as {output_file}")

        # Remove the temporary file
        os.remove(temp_file)

        return output_file
    except Exception as e:
        st.error(f"Error during video processing: {e}")
        return None

# Function to enhance images
def enhance_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    sharpening_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_sharpened = cv2.filter2D(img, -1, sharpening_kernel)
    enhanced_path = image_path.replace(".jpg", "_enhanced.png")
    cv2.imwrite(enhanced_path, img_sharpened)
    return enhanced_path

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
