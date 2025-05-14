from flask import Flask, request, jsonify
import whisper
import os
import tempfile

app = Flask(__name__)

# Load the Whisper model at startup
try:
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # Make sure this line doesn't conflict with local file names
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # Continue anyway so Flask can start - we'll handle the error in the endpoint
# Add this route to your transcriber/app.py

@app.route('/health', methods=['GET'])
def health_check():
    # Check if model is loaded successfully
    if 'model' in globals():
        return jsonify({"status": "healthy", "model_loaded": True}), 200
    else:
        return jsonify({"status": "unhealthy", "model_loaded": False}), 500
    
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        # Check if model is loaded
        if 'model' not in globals():
            return jsonify({"error": "Whisper model is not loaded"}), 500
            
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp:
            temp_path = temp.name
            audio_file.save(temp_path)
        
        # Transcribe the audio file
        print(f"Transcribing file: {temp_path}")
        result = model.transcribe(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        # Return the transcription result
        return jsonify({
            "text": result["text"],
            "segments": result.get("segments", []),
        })
        
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)