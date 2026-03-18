from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import wikipedia
import webbrowser
import os
import pywhatkit
import logging

# Import your existing VoiceAssistant class
from vois import VoiceAssistant   # <-- your file is named vois.py

app = Flask(__name__, static_folder=".")
CORS(app)

logging.basicConfig(level=logging.INFO)

# Create ONE shared assistant instance
assistant = VoiceAssistant()


# ── Serve the HTML file ──────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ── Main command endpoint (called from the browser) ──────
@app.route("/command", methods=["POST"])
def command():
    data = request.get_json()
    user_command = data.get("command", "").strip()

    if not user_command:
        return jsonify({"response": "No command received."})

    try:
        # Run through your existing Python logic
        response = assistant.process_command(user_command)
        return jsonify({"response": response})
    except Exception as e:
        logging.error(f"Command error: {e}")
        return jsonify({"response": "Sorry, something went wrong."})


# ── Optional: speak endpoint (triggers Python TTS) ───────
@app.route("/speak", methods=["POST"])
def speak_route():
    data = request.get_json()
    text = data.get("text", "")
    if text:
        assistant.speak(text)
    return jsonify({"status": "ok"})


# ── Time & Date endpoints ─────────────────────────────────
@app.route("/time")
def get_time():
    t = datetime.datetime.now().strftime("%I:%M %p")
    return jsonify({"response": f"The current time is {t}"})


@app.route("/date")
def get_date():
    d = datetime.datetime.now().strftime("%A, %B %d, %Y")
    return jsonify({"response": f"Today is {d}"})


if __name__ == "__main__":
    print("✅ Voice Assistant server running!")
    print("👉 Open your browser at:  http://127.0.0.1:5000")
    # Auto-open browser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False, port=5000)