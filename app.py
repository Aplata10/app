import os
import streamlit as st
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageEnhance
import subprocess

st.title("Drum Sheet Music Extractor")
st.markdown("""
Welcome **Drummer**! 🎶🥁

This app allows you to extract sheet music from drum tutorial videos and save it as a clean and clear PDF.
It's designed to work best with YouTube shorts that display drum sheet music on the screen.

Enter the link to your video below and start processing!
""")

# Only declare the video input box once
video_url = st.text_input("Enter YouTube video URL:")

st.header("Instructions")
st.markdown("""
1. Paste the link to a YouTube short containing sheet music.
2. Click **Process Video** and wait for the app to process the video.
3. Download your extracted file as a PDF.

### Recommended Video Types:
