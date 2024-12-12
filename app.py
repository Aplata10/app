import os
import cv2
import pytesseract
from PIL import Image
import streamlit as st
from tempfile import NamedTemporaryFile
import subprocess

# Function to download and convert video
def download_video(url):
    temp_file = "temp_video.webm"
    output_file = "downloaded_video.mp4"

    try:
        # Check if yt-dlp is installed
        yt_dlp_check = os.system("yt-dlp --version")
        if yt_dlp_check != 0:
            st.error("yt-dlp is not installed. Please install it and try again.")
            return None

        # Check if ffmpeg is installed
        ffmpeg_check = os.system("ffmpeg -version")
        if ffmpeg_check != 0:
            st.error("ffmpeg is not installed. Please install it and try again.")
            return None

        # Use yt-dlp to download the video
        download_command = f"yt-dlp -f best -o {temp_file} {url}"
        if os.system(download_command) != 0:
            st.error("Failed to download the video. Check the URL and try again.")
            return None

        # Convert the downloaded video to MP4 using ffmpeg
        convert_command = f"ffmpeg -i {temp_file} -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac {output_file}"
        if os.system(convert_command) != 0:
            st.error("Failed to convert the video to MP4 format.")
            return None

        # Cleanup the temporary file
        os.remove(temp_file)
        return output_file

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
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
