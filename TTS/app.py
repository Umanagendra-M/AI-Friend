from flask import Flask, request, jsonify, send_file
import os
from gtts import gTTS
import logging
import subprocess
import io

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Use gTTS to synthesize speech
    try:
        shared_tts_dir = '/app/shared_tts'
        logger.info (f"Checking if the directory, {shared_tts_dir} exists")
        os.makedirs(shared_tts_dir, exist_ok=True)  # Create directory if it doesn't exist
        
        # generate a new file for gtts and ffmpeg to work with
        temp_mp3_file = os.path.join(shared_tts_dir, 'temp.mp3')
        output_wav_file = os.path.join(shared_tts_dir, 'output.wav')

        tts = gTTS(text=text, lang='en')
        tts.save(temp_mp3_file)

        # Convert the audio using ffmpeg
        ffmpeg_command = [
            "ffmpeg",
            "-y", # This is useful as gTTS saves to a temp file
            "-i", temp_mp3_file,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_wav_file
        ]
        
        # Run command then wait
        subprocess.run(ffmpeg_command, check=True)

        logger.info(f"Returning file: {output_wav_file}")
        # Return .wav data
        return send_file(output_wav_file, mimetype="audio/wav")

    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')