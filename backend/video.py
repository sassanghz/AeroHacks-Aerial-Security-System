import cv2
import json
import time
import threading
from flask import Flask, Response, jsonify
from faceAnalyze import analyzeImage

app = Flask(__name__)

video_source = "frontend/public/videos/source.mp4"  # or 0 / RTSP URL
cap = cv2.VideoCapture(video_source)

if not cap.isOpened():
    raise RuntimeError("Could not open video source")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

frame_lock = threading.Lock()
analysis_lock = threading.Lock()

latest_frame_jpeg = None
latest_analysis = {
    "age": "No Intruder Detected",
    "skin_tone": "No Intruder Detected",
    "facial_features": ["No Intruder Detected"],
    "clothing": ["No Intruder Detected"],
    "injuries_or_condition": ["No Intruder Detected"],
    "uncertainty": ["No Intruder Detected"],
    "frame_id": 0,
    "updated_at": 0,
}
analysis_version = 0


def save_analysis_to_file(data):
    with open("analysis.json", "w") as f:
        json.dump(data, f, indent=2)


def process_video():
    global latest_frame_jpeg, latest_analysis, analysis_version

    last_analysis_time = 0
    frame_id = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_id += 1
        current_time = time.time()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=7,
            minSize=(80, 80)
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 170), 2)

        cv2.putText(
            frame,
            "LIVE ANALYSIS",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 170),
            2
        )

        ok, buffer = cv2.imencode(".jpg", frame)
        if ok:
            with frame_lock:
                latest_frame_jpeg = buffer.tobytes()

        should_analyze = (current_time - last_analysis_time) >= 5

        if should_analyze:
            snapshot_path = f"images/frame_{int(current_time)}.jpg"
            cv2.imwrite(snapshot_path, frame)

            try:
                result = analyzeImage(snapshot_path)

                result["frame_id"] = frame_id
                result["updated_at"] = current_time

                with analysis_lock:
                    latest_analysis = result
                    analysis_version += 1

                save_analysis_to_file(result)
                last_analysis_time = current_time

            except Exception as e:
                print("Analysis error:", e)

        time.sleep(0.03)
