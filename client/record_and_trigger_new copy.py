import os
import uuid
import wave
import pyaudio
import requests
import logging
import argparse
import time
#import threading
import audioop
import numpy as np  # Import numpy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriberClient:
    def __init__(self, url="http://localhost:8001"):
        """Initialize with transcriber service URL"""
        self.url = url
        logger.info(f"Initialized Transcriber client with URL: {self.url}")

    def transcribe_audio(self, audio_file):
        """Transcribe audio using the transcriber API"""
        try:
            files = {"audio": audio_file}
            response = requests.post(f"{self.url}/transcribe", files=files)

            if response.status_code == 200:
                result = response.json()
                logger.info("Transcription successful")
                return result
            else:
                logger.error(f"Transcription failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
    
        except Exception as e:
            logger.error(f"Error sending audio to transcriber: {e}")
            return None

class OllamaClient:
    def __init__(self, url="http://localhost:11434"):
        """Initialize with Ollama API URL"""
        self.url = url
        logger.info(f"Initialized Ollama client with URL: {self.url}")

    def generate_text(self, prompt, model="llama2", stream=False, context=None):
        """Generate text using the Ollama API"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }

            if context:
                payload["context"] = context

            logger.info(f"Sending prompt to Ollama API")

            response = requests.post(
                f"{self.url}/api/generate",
                json=payload,
                timeout=60)
    
            if response.status_code == 200:
                result = response.json()
                logger.info("Ollama processing successful")
                return result
            else:
                logger.error(f"Ollama processing failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error sending text to Ollama: {e}")
            return None

class VoiceRecorder:
    def __init__(self,
                 rate=16000,
                 chunk=1024,
                 channels=1,
                 format=pyaudio.paInt16,
                 transcriber_url="http://localhost:8001",
                 ollama_url="http://localhost:11434",
                 tts_url="http://localhost:8003",
                 shared_dir="./shared",
                 silence_threshold=500,
                 silence_duration=10,
                 recording_timeout=300):  # Maximum recording time in seconds
        """Initialize voice recorder with audio parameters and service URLs"""
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.format = format
        self.frames = []
        self.stream = None
        self.audio = None
        self.shared_dir = shared_dir
        temp_file = os.path.join(self.shared_dir, "temp_recording.wav")
        self.temp_wav_file = temp_file.replace("\\", "/")
        self.is_recording = False
        self.last_audio_time = None
        self.SILENCE_THRESHOLD = silence_threshold  # Adjust based on your microphone and environment
        self.SILENCE_DURATION = silence_duration  # Seconds of silence to trigger end of recording
        self.RECORDING_TIMEOUT = recording_timeout # Set the Time
        self.start_time=time.time()
        logger.info (f"Silence threshold is {self.SILENCE_DURATION} time {self.RECORDING_TIMEOUT}") #Log checks

        # Initialize service clients
        self.transcriber = TranscriberClient(url=transcriber_url)
        self.ollama = OllamaClient(url=ollama_url)
        self.tts_url = tts_url
    def is_silent(self, data):
        """Determines if the audio chunk is silence based on threshold."""
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.abs(audio_data).mean() < self.SILENCE_THRESHOLD

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback function for PyAudio stream."""
        # Calculate the volume (RMS) of the audio chunk
        rms = audioop.rms(in_data, 2)  # Assuming 2 bytes per sample (paInt16)

        # See and trigger base information if there are any
        if rms > self.SILENCE_THRESHOLD: #Set RMS
            self.last_audio_time = time.time() #Set to last time.
            self.frames.append(in_data) #Then add

        #See if no last audiotime
        elif self.last_audio_time is None: #If there is new message, make it to zero to be ready
            self. last_audio_time = time.time()

        #Otherwise check and do nothing
        
        elif (time.time() - self.last_audio_time) > self.SILENCE_DURATION:
            print("Silence detected, stopping recording.")
            return (in_data, pyaudio.paComplete)
        return (in_data, pyaudio.paContinue)

    def start_recording(self):
        """Start recording audio from microphone."""
        if self.is_recording:
            print("Already recording!")
            return

        print("Starting recording... Speak now.")
        self.is_recording = True
        self.frames = []
        self.last_audio_time = 0

        # Open audio stream
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                stream_callback=self._audio_callback
            )
            self.stream.start_stream()
        except Exception as e:
            logger.error(f"Error starting the stream {e}")
        """Start recording audio from microphone."""
    
    def stop_recording(self):
        """Stop recording audio and save the audio to a WAV file."""
        if not self.is_recording:
            return

        print("Stopping recording...")
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Save audio data to WAV file
        if self.frames:
            try:
                wf = wave.open(self.temp_wav_file, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
                wf.close()
                print(f"Saved recording to {self.temp_wav_file}")
                return self.temp_wav_file
            except Exception as e:
                logger.error(f"Error saving audio: {e}")
        else:
            print("No audio recorded.")
        return None

    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    def process_audio(self, model="llama2"):
        """Process audio through transcription and LLM"""
        result = {}
        print ("Processing audio, please speak to trigger the system")

        result = {} #For results

        # 1: Start process here
        try: #Open audio stream
            print ("Starting to record if has access to the system")
            self.audio = pyaudio.PyAudio()
            print ("Started the audio")
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                stream_callback=self._audio_callback
    )
            self.stream.start_stream()
            print ("Started the streams")
        except Exception as e:
            logger.error(f"Error starting the stream {e}")
            result["error"] = f"Error during stream creation {e}"
            return result #It cannot be created to cannot proceed further

        #Loop to run and see what happens. There needs to be two breaks, and for the call.  You have to say or terminate via keyboard interrup
        try: #Check to ensure it continues run unless there is some interuption
            while self.is_recording:
                if (time.time() - self.start_time) > 5:
                    break
                time.sleep (1) #Let it breathe and pass on to next action
        except KeyboardInterrupt:
            print ("Keyboard Interupted")
        except Exception as e:
            logger.exception ("Error happened in process audio")
        # Stop recording and save audio file
        print ("Stopping and saving")
        audio_file = self.stop_recording()
        print ("Stopping and saved")

        if not audio_file:
            result["error"] = "No audio recorded"
            return result
        try:
            with open(audio_file, 'rb') as f:
                print ("Calling transcriber")
                transcription_result = self.transcriber.transcribe_audio(f)
                print ("Called transcriber")
        except Exception as e:
            logger.error(f"Error opening audio file: {e}")
            result["error"] = f"Error opening audio file: {e}"
            return result

        if not transcription_result:
            result["error"] = "Transcription failed"
            return result

        result["transcription"] = transcription_result

        prompt = f"you are a friendly conversation bot that helps people get clarity in the schedule for the day be positive and encouraging {transcription_result.get('text', '')}"
        logger.info(f"Generated Prompt: {prompt}")

        try:
            # Get LLM response
            print ("Calling LLM")
            llm_response = self.ollama.generate_text(prompt, model=model)
            print ("Called LLM")

            if llm_response is None:
                logger.error("Ollama generate_text returned None.")
                result["error"] = "Ollama processing failed"
                return result

            result["llm_response"] = llm_response
            llm_text = llm_response.get("response", "")
            logger.info(f"LLM Response for TTS: {llm_text}")

            # Synthesize speech using the TTS service
            try:
                print ("Calling TTS")
                tts_response = requests.post(
                    self.tts_url + "/synthesize",
                    json={"text": llm_text},
                    stream=True)
                print ("Called TTS")

                logger.info(f"TTS Response Status Code: {tts_response.status_code}")

                if tts_response.status_code == 200:
                    # Save the audio to a local file
                    print ("Saving to audio file")
                    audio_data = tts_response.raw.read()  # Read all audio data
                    local_audio_dir = "./llm_audio" # local audio dir
                    os.makedirs(local_audio_dir, exist_ok=True) # Make the directory if it does not exist
                    audio_filename = os.path.join(local_audio_dir, f"llm_audio_{uuid.uuid4()}.wav") # Unique audio file

                    with open(audio_filename, "wb") as f:
                        f.write(audio_data)
                    print ("Saved to audio file")

                    logger.info(f"Audio saved to {audio_filename}")
                    result["tts_success"] = True

                    # Play the audio from local using stream:
                    try:
                        wf = wave.open(audio_filename, 'rb')
                        p = pyaudio.PyAudio()
                        # Get the audio format from the wave file
                        format = p.get_format_from_width(wf.getsampwidth())
                        channels = wf.getnchannels()
                        rate = wf.getframerate()

                        stream = p.open(format=format,
                                        channels=channels,
                                        rate=rate,
                                        output=True)

                        chunk_size = 1024  # Adjust chunk size as needed
                        print ("Playing with stream")
                        # Read data from the stream in chunks and play it
                        data = wf.readframes(chunk_size)
                        while data:
                            stream.write(data)
                            data = wf.readframes(chunk_size)

                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        wf.close()
                        print ("Played with stream")

                        logger.info("Audio stream playback completed.")
                    except Exception as e:
                        logger.error(f"Error playing audio stream: {e}")
                        result["error"] = f"Error playing audio stream: {e}"
                else:
                    logger.error(f"TTS synthesis failed with status code: {tts_response.status_code}")
                    result["error"] = f"TTS synthesis failed: {tts_response.status_code}"

            except Exception as tts_error:
                logger.exception(f"Error during TTS processing: {tts_error}")
                result["error"] = f"TTS processing error: {tts_error}"
        except Exception as e:
            logger.exception("Error during Ollama processing:")
            result["error"] = f"Ollama processing error: {str(e)}"

        return result
def main():
    parser = argparse.ArgumentParser(description="Record audio and process with transcription and LLM")
    parser.add_argument("--transcriber-url", default="http://localhost:8001", help="Transcriber service URL")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--tts-url", default="http://localhost:8003", help="TTS service URL")
    parser.add_argument("--model", default="llama3.2", help="Ollama model to use")
    parser.add_argument("--shared-dir", default="./shared", help="Shared directory")
    parser.add_argument("--silence-threshold", type=int, default=100, help="Silence threshold")
    parser.add_argument("--silence-duration", type=float, default=5.0, help="Silence timeout in seconds")
    args = parser.parse_args()

    print("=== Voice Interview Bot ===")

    # Initialize recorder with service URLs
    recorder = VoiceRecorder(
        transcriber_url=args.transcriber_url,
        ollama_url=args.ollama_url,
        tts_url=args.tts_url,
        shared_dir=args.shared_dir,
        silence_threshold=args.silence_threshold,
        silence_duration=args.silence_duration
    )

    # Main loop
    while True:
        print("Listening for initial speech... Speak now.")

        recorder.start_recording()

        # Wait for recording to complete in callback
        time.sleep(recorder.SILENCE_DURATION + 1)
        # Process the audio
        result = recorder.process_audio(model=args.model)

        if result and "error" not in result:
            # Display results
                print("\n=== Results ===")

                if "transcription" in result:
                    print("\nTranscription:")
                    print(result["transcription"].get("text", "No text transcribed"))

                if "llm_response" in result:
                    print("\nLLM Response:")
                print(result["llm_response"].get("response", "No response generated"))

                if "error" in result:
                    print(f"\nError: {result['error']}")
        else:
            print("Processing failed completely")

        #Clean values to reset values
        #These valuees cause the issue.
        recorder.frames = []
        recorder.last_audio_time = None

        #Recorder end is now over
        recorder.cleanup()
if __name__ == "__main__":
    main()

