from flask import Flask, jsonify
from flask_cors import CORS
from note_detector import NoteDetector

app = Flask(__name__)
CORS(app)

note_detector = NoteDetector()

@app.route('/record', methods=['POST'])
def record_and_detect():
    try:
        # Record audio and detect notes
        audio = note_detector.record_audio(duration=3)
        notes = note_detector.detect_notes(audio)
        
        return jsonify({
            'success': True,
            'notes': notes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 