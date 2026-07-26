const BACKEND_URL = "https://vigileye-production.up.railway.app/analyze"; 
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startBtn = document.getElementById('startBtn');
const statusDiv = document.getElementById('status');
const earDisplay = document.getElementById('ear-display');
const alarmSound = document.getElementById('alarmSound');
const EAR_THRESHOLD = 0.21;
const CLOSED_TIME_LIMIT = 1500;   // ms - eyes closed alert
const MAR_THRESHOLD = 0.5;        // tune after testing your own yawns
const YAWN_TIME_LIMIT = 1000;     // ms - mouth open alert
const HEAD_TILT_THRESHOLD = 15;   // degrees of downward pitch (tune based on testing)
const TILT_TIME_LIMIT = 1500;     // ms - head tilted alert

let eyesClosedStart = null;
let yawnStart = null;
let tiltStart = null;
let alertPlaying = false;
let intervalId = null;
let isRequestPending = false;

startBtn.addEventListener('click', async () => {

    try {

        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        startBtn.textContent = "Camera Running";
        startBtn.disabled = true;

        // capture + send a frame every 300ms

        intervalId = setInterval(captureAndAnalyze, 1000);

    } catch (err) {

        statusDiv.textContent = "Camera access denied or unavailable";
        console.error(err);

    }

});

function captureAndAnalyze() {
    if (isRequestPending) return;  // skip this cycle if previous request hasn't finished yet
    isRequestPending = true;

    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg', 0.6);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // force-cancel after 30s (Render free tier can be slow)

    fetch(BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData }),
        signal: controller.signal
    })
    .then(res => res.json())
    .then(data => {
        clearTimeout(timeoutId);
        handleResult(data);
        isRequestPending = false;
    })
    .catch(err => {
        clearTimeout(timeoutId);
        console.error("Backend error:", err);
        isRequestPending = false;  // always reset, even on timeout/failure
    });
}

function handleResult(data) {

    if (!data.face_detected) {

        statusDiv.textContent = "No Face Detected";
        statusDiv.className = "status warning";
        earDisplay.textContent = "EAR: -- | MAR: -- | Tilt: --";

        eyesClosedStart = null;
        yawnStart = null;
        tiltStart = null;

        return;

    }

    earDisplay.textContent = `EAR: ${data.ear} | MAR: ${data.mar} | Head Pitch: ${data.head_pitch}°`;

    let triggers = [];  // collect which signals are currently past their time limit

    // --- Eyes closed check ---

    if (data.ear < EAR_THRESHOLD) {

        if (eyesClosedStart === null) eyesClosedStart = Date.now();
        if (Date.now() - eyesClosedStart >= CLOSED_TIME_LIMIT) triggers.push("Eyes Closed");

    } else {

        eyesClosedStart = null;

    }

    // --- Yawn check ---

    if (data.mar > MAR_THRESHOLD) {

        if (yawnStart === null) yawnStart = Date.now();
        if (Date.now() - yawnStart >= YAWN_TIME_LIMIT) triggers.push("Yawning");

    } else {

        yawnStart = null;

    }

    // --- Head tilt check (positive pitch = looking down, common when dozing off) ---

    if (Math.abs(data.head_pitch) > HEAD_TILT_THRESHOLD) {

        if (tiltStart === null) tiltStart = Date.now();
        if (Date.now() - tiltStart >= TILT_TIME_LIMIT) triggers.push("Head Tilted");

    } else {

        tiltStart = null;

    }

    // --- Combine results ---

    if (triggers.length > 0) {

        statusDiv.textContent = `DROWSY ALERT! (${triggers.join(", ")})`;
        statusDiv.className = "status drowsy";

        if (!alertPlaying) {

            alarmSound.play();
            alertPlaying = true;

        }

    } else if (eyesClosedStart || yawnStart || tiltStart) {

        // something is happening but hasn't crossed the time limit yet

        statusDiv.textContent = "Monitoring...";
        statusDiv.className = "status warning";
        alertPlaying = false;

    } else {

        statusDiv.textContent = "Active";
        statusDiv.className = "status active";
        alertPlaying = false;

    }

}
