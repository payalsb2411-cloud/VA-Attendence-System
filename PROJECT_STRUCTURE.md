# Project Structure

```text
attendance system/
  server/
    app.py              # Browser app + API server
    __init__.py
  streamlit_app.py     # Streamlit browser app
  src/
    capture_faces.py    # Face sample capture
    train_model.py      # Model training
    mark_attendance.py  # Face recognition attendance
    gui_app.py          # Desktop GUI
    data_store.py       # Shared CSV readers
  android-app/          # Android client scaffold
  data/                 # Employee data and captured samples
  attendance/           # Daily attendance CSV files
  models/               # Trained face model and labels
  README.md             # Quick setup
  DEPLOYMENT.md         # How to publish the app
  start_app.ps1         # One-command launcher
  start_streamlit.ps1   # Streamlit launcher
```

Main browser app:
- Open `http://<server-ip>:8000/`
- Use the page on desktop or mobile
- Capture photos directly from the browser
