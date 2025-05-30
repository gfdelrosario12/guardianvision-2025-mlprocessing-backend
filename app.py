from flask import Flask, request, jsonify
import boto3
import os
import time
from datetime import datetime
from pydub import AudioSegment
from io import BytesIO
import uuid

app = Flask(__name__)

# === AWS S3 Config ===
S3_BUCKET = os.environ.get('S3_BUCKET', 'your-bucket-name')  # default bucket for testing
s3 = boto3.client('s3')

# === In-memory metadata stores ===
AUDIO_METADATA = []
VIDEO_METADATA = []
GPS_METADATA = []

@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    file = request.data
    timestamp = datetime.utcnow().isoformat()
    filename = f"audio/{uuid.uuid4()}_{timestamp}.raw"

    # Upload to S3
    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file)

    # Save metadata
    AUDIO_METADATA.append({'key': filename, 'timestamp': timestamp})
    print(f"Audio uploaded: {filename}")
    return jsonify({"status": "ok", "s3_key": filename}), 200

@app.route('/upload/video', methods=['POST'])
def upload_video():
    file = request.data
    timestamp = datetime.utcnow().isoformat()
    filename = f"video/{uuid.uuid4()}_{timestamp}.jpg"

    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file)
    VIDEO_METADATA.append({'key': filename, 'timestamp': timestamp})
    print(f"Video uploaded: {filename}")
    return jsonify({"status": "ok", "s3_key": filename}), 200

@app.route('/upload/gps', methods=['POST'])
def upload_gps():
    gps_data = request.get_json()
    timestamp = datetime.utcnow().isoformat()
    filename = f"gps/{uuid.uuid4()}_{timestamp}.json"

    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=str(gps_data))
    GPS_METADATA.append({'key': filename, 'timestamp': timestamp, 'data': gps_data})
    print(f"GPS uploaded: {filename}")
    return jsonify({"status": "ok", "s3_key": filename}), 200

@app.route('/analyze/audio', methods=['GET'])
def analyze_audio():
    trigger_word = "help"
    print(f"Looking for trigger word: {trigger_word}")

    if AUDIO_METADATA:
        trigger_index = len(AUDIO_METADATA) // 2
        trigger_entry = AUDIO_METADATA[trigger_index]
        trigger_time = datetime.fromisoformat(trigger_entry['timestamp'])

        def in_range(entry):
            t = datetime.fromisoformat(entry['timestamp'])
            delta = (t - trigger_time).total_seconds()
            return -1800 <= delta <= 1800

        audio_files = [e for e in AUDIO_METADATA if in_range(e)]
        video_files = [e for e in VIDEO_METADATA if in_range(e)]
        gps_points  = [e for e in GPS_METADATA if in_range(e)]

        return jsonify({
            "trigger_time": trigger_time.isoformat(),
            "audio_files": audio_files,
            "video_files": video_files,
            "gps_points": gps_points
        }), 200

    return jsonify({"error": "No audio metadata"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)