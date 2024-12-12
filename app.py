st.title("Drum Sheet Music Extractor")
st.markdown("""
Welcome **Drummer**! 🎶🥁

This app allows you to extract sheet music from drum tutorial videos and save it as a clean and clear PDF.
It's designed to work best with YouTube shorts that display drum sheet music on the screen.
""")

# Position the input and button together at the top
video_url = st.text_input("Enter YouTube video URL:")
if st.button("Process Video"):
    with st.spinner("Downloading and processing video..."):
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
            total_pages = 4  # Example: Replace with dynamic logic using `extract_total_pages` if needed
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

# Instructions and Examples Section
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
