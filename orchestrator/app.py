import os
import tempfile
import requests
import ffmpeg
from flask import Flask, request, jsonify, send_file
import uuid

app = Flask(__name__)

# Service URLs
TRANSCRIBER_URL = os.environ.get("TRANSCRIBER_URL", "http://transcriber:8001")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:8002")
TTS_URL = os.environ.get("TTS_URL", "http://tts:8003")

@app.route('/health', methods=['GET'])
def health_check():
    try:
        transcriber_response = requests.get(f"{TRANSCRIBER_URL}/health", timeout=5)
        transcriber_healthy = transcriber_response.status_code == 200

        ollama_response = requests.get(f"{OLLAMA_URL}/health", timeout=5)
        ollama_healthy = ollama_response.status_code == 200

        tts_response = requests.get(f"{TTS_URL}/health", timeout=5)
        tts_healthy = tts_response.status_code == 200

        return jsonify({
            "status": "healthy" if all([transcriber_healthy, ollama_healthy, tts_healthy]) else "degraded",
            "transcriber_connection": transcriber_healthy,
            "ollama_connection": ollama_healthy,
            "tts_connection": tts_healthy,
            "transcriber_status": transcriber_response.json() if transcriber_healthy else None,
            "ollama_status": ollama_response.json() if ollama_healthy else None
        }), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

def convert_to_pcm_mono_16k(input_path, output_path):
    """Convert audio to 16-bit PCM, mono, 16kHz using ffmpeg."""
    ffmpeg.input(input_path).output(
        output_path,
        acodec='pcm_s16le',
        ar='16000',
        ac=1
    ).overwrite_output().run(quiet=True)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    """Process audio file: transcribe, generate response, and synthesize speech"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files['file']
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, "input.wav")
    converted_path = os.path.join(temp_dir, "converted_input.wav")
    audio_file.save(input_path)

    try:
        # Convert uploaded audio to PCM 16-bit mono 16kHz
        convert_to_pcm_mono_16k(input_path, converted_path)

        # Step 1: Send to transcriber
        with open(converted_path, 'rb') as f:
            transcribe_response = requests.post(
                f"{TRANSCRIBER_URL}/transcribe", 
                files={"file": f}
            )

        if transcribe_response.status_code != 200:
            return jsonify({"error": "Transcription failed", "details": transcribe_response.text}), 500

        transcript = transcribe_response.json().get("text", "")

        # Step 2: Generate AI response
        ollama_response = requests.post(
            f"{OLLAMA_URL}/generate",
            json={
                "prompt": transcript,
                "system_prompt": "You are a helpful voice assistant. Keep responses concise and conversational."
            }
        )

        if ollama_response.status_code != 200:
            return jsonify({"error": "AI response generation failed", "details": ollama_response.text}), 500

        ai_response = ollama_response.json().get("response", "I'm sorry, I couldn't process that.")

        # Step 3: TTS synthesis
        tts_response = requests.post(
            f"{TTS_URL}/synthesize",
            json={"text": ai_response}
        )

        if tts_response.status_code != 200:
            return jsonify({"error": "Speech synthesis failed", "details": tts_response.text}), 500


# Get audio file name from TTS service
        audio_file_name = tts_response.json().get("audio_file")

# Download the audio from TTS
        tts_audio_response = requests.get(f"{TTS_URL}/audio/{audio_file_name}", stream=True)
        raw_tts_path = os.path.join(temp_dir, f"raw_tts_{uuid.uuid4()}.wav")

        with open(raw_tts_path, "wb") as f:
            f.write(tts_audio_response.content)

        # Convert it to PCM 16-bit mono 16kHz
        converted_tts_path = os.path.join(temp_dir, f"converted_tts_{uuid.uuid4()}.wav")
        convert_to_pcm_mono_16k(raw_tts_path, converted_tts_path)

        return jsonify({
            "success": True,
            "transcript": transcript,
            "response_text": ai_response,
            "audio_file": os.path.basename(converted_tts_path),
            "audio_url": f"/play_response/{os.path.basename(converted_tts_path)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Optional cleanup
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(converted_path): os.remove(converted_path)

@app.route('/play_response/<filename>', methods=['GET'])
def play_response(filename):
    try:
        response = requests.get(f"{TTS_URL}/audio/{filename}", stream=True)
        return send_file(
            response.raw,
            mimetype=response.headers.get('content-type', 'audio/wav'),
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
