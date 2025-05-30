from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for frontend

# Store metadata in-memory for demo (consider DB in production)
TRIGGER_EVENTS = []

@app.route('/trigger', methods=['POST'])
def receive_trigger():
    data = request.get_json()
    if not data or 'filename' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    event_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    event = {
        "id": event_id,
        "filename": data['filename'],
        "timestamp": data['timestamp'],
        "latitude": data.get('latitude'),
        "longitude": data.get('longitude'),
        "received_at": timestamp
    }

    TRIGGER_EVENTS.append(event)

    print(f"Received trigger event: {event}")

    # Emit event to all connected websocket clients
    socketio.emit('trigger_event', event, broadcast=True)

    return jsonify({"status": "trigger received", "id": event_id}), 200

# Optional: websocket event when client connects
@socketio.on('connect')
def on_connect():
    print('Client connected')
    # Optionally send existing events on connection
    emit('all_triggers', TRIGGER_EVENTS)

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Use eventlet for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000)
