 VigilEye — Real-Time Driver Drowsiness Detection System
A full-stack computer vision system that monitors driver alertness in real time using facial landmark detection, and triggers instant audio-visual alerts before drowsiness becomes dangerous.

  

🔗 [Try it live →](https://vigiley.netlify.app/)


# Overview
Drowsy driving is one of the leading causes of road accidents worldwide, often striking without warning. VigilEye addresses this by continuously analyzing a driver's face through their webcam — tracking eye closure, yawning, and head posture — to detect the earliest physical signs of fatigue and alert the driver before it's too late.

Unlike simple demos, VigilEye is architected as a genuine full-stack, deployed web application: a browser-based frontend that works on any device with a camera, talking in real time to a dedicated computer vision backend — no installation required for the end user.


# Features
** Eye Closure Detection — Calculates Eye Aspect Ratio (EAR) from 468-point facial landmarks to detect sustained eye closure
** Yawn Detection — Tracks Mouth Aspect Ratio (MAR) to identify yawning, a key drowsiness indicator
** Head Tilt / Nodding Detection — Uses 3D head pose estimation (via solvePnP) to catch the head-drooping motion common when dozing off
** Real-Time Audio-Visual Alerts — Instant on-screen warning and alarm sound the moment any drowsiness signal crosses its threshold
** Fully Browser-Based — No app installation needed; works directly from any device's camera via the browser
** Multi-Signal Robustness — Combines three independent signals (eyes, mouth, head pose), so the system stays useful even if one signal is temporarily unreliable (e.g., dark sunglasses affecting eye tracking)


# Architecture
VigilEye is built as two independently deployed services communicating over a REST API:

┌─────────────────────────┐         ┌──────────────────────────────┐

│   FRONTEND (Netlify)     │  POST   │   BACKEND (Railway)           │

│   HTML / CSS / JS        │ ──────► │   Flask + OpenCV + Mediapipe  │

│                          │  image  │                                │

│  • Captures webcam frame │         │  • Face mesh detection         │

│    every 300ms           │         │  • EAR / MAR calculation       │

│  • Tracks alert timers   │ ◄────── │  • Head pose estimation        │

│  • Triggers alarm + UI   │  JSON   │  • Returns metrics as JSON     │

└─────────────────────────┘         └──────────────────────────────┘

Why this architecture? Separating concerns this way mirrors real-world production systems — a lightweight, globally-distributed static frontend paired with a dedicated backend service for heavy computation, rather than bundling everything into one monolith.


# Tech Stack
Layer
Technology
Frontend
HTML5, CSS3, Vanilla JavaScript
Backend
Python, Flask, Gunicorn
Computer Vision
OpenCV, Mediapipe (Face Mesh — 468-point landmark model)
Deployment
Netlify (frontend), Railway (backend, Dockerized)
Core Techniques
Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR), solvePnP head pose estimation

**Live Services:**
- Frontend: [vigiley.netlify.app](https://vigiley.netlify.app)
- Backend API: [vigileye-production.up.railway.app](https://vigileye-production.up.railway.app)


# How It Works
The frontend captures a frame from the user's webcam every 300ms and sends it as a base64-encoded image to the backend via a REST API call.
The backend runs Mediapipe's Face Mesh model on the frame, extracting 468 facial landmarks.
From these landmarks, the backend computes:
EAR (Eye Aspect Ratio) — from eye corner and eyelid landmarks
MAR (Mouth Aspect Ratio) — from lip landmarks
Head Pitch — via solvePnP, mapping 2D facial landmarks to a 3D head model
These metrics are returned as JSON to the frontend.
The frontend independently tracks how long each metric has been past its drowsiness threshold. If any signal (eyes closed, yawning, or head tilted) is sustained past its time limit, a visual and audio alert fires immediately.


# Run It Locally
Backend
cd backend

python -m venv venv

venv\Scripts\activate        # Windows

# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

python app.py
Frontend
Open frontend/index.html with VS Code's Live Server extension (or any static server).

Update the BACKEND_URL in frontend/script.js to point to your local backend (http://localhost:5000/analyze) when testing locally.


# Engineering Challenges Solved
Building and deploying this project surfaced several real-world engineering problems beyond the core computer vision logic:

Cross-service architecture: Designed and connected a decoupled frontend/backend system communicating over HTTPS with proper CORS handling
Resource-constrained deployment: Diagnosed and resolved memory and CPU timeout issues on free-tier cloud hosting by optimizing frame resolution, disabling unnecessary landmark refinement, and tuning server worker configuration
Dependency and environment management: Solved Python version mismatches and native library dependency issues (system-level libraries required by OpenCV) inside containerized deployments
Request lifecycle management: Implemented request-locking and timeout handling on the frontend to prevent overlapping API calls from exhausting browser resources
Graceful degradation: Designed the multi-signal detection logic so the system remains useful even when one signal (e.g., eye visibility with dark sunglasses) is compromised

# License
This project is open source and available for learning and reference purposes.



**Built by Harshada** — [GitHub](https://github.com/harshada8983)

