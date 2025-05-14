import pyaudio
import wave
import numpy as np
import os
import time
import threading

class VoiceRecorder:
    def __init__(self):
        # Audio recording parameters
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.SILENCE_THRESHOLD = 500  # Adjust based on your microphone and environment
        self.SILENCE_DURATION = 2.0  # Seconds of silence to trigger end of recording
        
        # File paths
        self.temp_dir = "C:/Users/umall/Documents/github_projects/voice_interview_bot_setup/voice_interview_bot/shared"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_wav_file = os.path.join(self.temp_dir, "input.wav")
        
        # State variables
        self.is_recording = False
        self.frames = []
        self.last_audio_time = 0
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def is_silent(self, data):
        """Determines if the audio chunk is silence based on threshold."""
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.abs(audio_data).mean() < self.SILENCE_THRESHOLD
    
    def start_recording(self):
        """Start recording audio from microphone."""
        if self.is_recording:
            print("Already recording!")
            return
        
        print("Starting recording... Speak now.")
        self.is_recording = True
        self.frames = []
        self.last_audio_time = time.time()
        
        # Open audio stream
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for the audio stream."""
        if not self.is_silent(in_data):
            self.last_audio_time = time.time()
        
        self.frames.append(in_data)
        
        # Check if we've had silence for SILENCE_DURATION seconds
        if time.time() - self.last_audio_time > self.SILENCE_DURATION:
            # Use threading to stop recording to avoid blocking in the callback
            threading.Thread(target=self.stop_recording).start()
        
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self):
        """Stop recording and save the audio to a WAV file."""
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
            wf = wave.open(self.temp_wav_file, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            print(f"Saved recording to {self.temp_wav_file}")
            
            # Return the path to the recording
            return self.temp_wav_file
        else:
            print("No audio recorded.")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.close()
        self.audio.terminate()
        # Optionally clean up temp files
        # if os.path.exists(self.temp_wav_file):
        #     os.remove(self.temp_wav_file)

def main():
    recorder = VoiceRecorder()
    
    try:
        print("Voice Recorder Ready!")
        print("Press Ctrl+C to exit")
        
        while True:
            # Wait for user input to start recording
            input("Press Enter to start recording...")
            recorder.start_recording()
            
            # Wait for recording to complete
            while recorder.is_recording:
                time.sleep(0.1)
            
            print("Recording finished. Audio saved to:", recorder.temp_wav_file)
            
            # Ask if user wants to continue
            choice = input("Continue recording? (y/n): ")
            if choice.lower() != 'y':
                break
                
    except KeyboardInterrupt:
        print("\nStopping recorder...")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()