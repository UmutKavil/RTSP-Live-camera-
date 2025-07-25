RTSP Viewer Pro - Python Application

Features
✔  This Python application is a GUI tool developed for viewing video streams over RTSP protocol. Key features include:
✔  RTSP Stream Viewing: Displays real-time video streams at 1280x720 resolution
✔  Connection Testing: Built-in camera connection testing functionality
✔  User-Friendly Interface: Custom Matplotlib-based GUI
✔  Performance Monitoring: Real-time FPS (frames per second) tracking
✔  Multi-Threading: Stream processing without blocking the main UI
✔  Error Handling: Detailed error messages and status information

Technology Stack
✔ Python 3.x
✔ FFmpeg (for video stream processing)
✔ NumPy (image processing)
✔ Matplotlib (GUI and visualization)
✔ Tkinter (URL input dialog)

Installation
1.Install requirements:
pip install ffmpeg-python numpy matplotlib
2.Ensure FFmpeg is installed on your system

Usage
python rtsp_viewer.py
✔ Use "Change URL" button to enter RTSP stream URL
✔ Click "Start" button to begin streaming
✔ Use "Test Connection" to verify camera connectivity
✔ Click "CLOSE" button to terminate the application
