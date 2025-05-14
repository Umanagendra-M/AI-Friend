import wave

audio_filename = 'C:/Users/umall/Documents/github_projects/voice_interview_bot_setup/voice_interview_bot/client/llm_audio/llm_audio_e274f053-fc6c-43a3-8ca4-c8875328d27c.wav'

with wave.open(audio_filename, 'rb') as wf:
    print("Channels:", wf.getnchannels())
    print("Sample Width:", wf.getsampwidth())
    print("Framerate:", wf.getframerate())
    print("Frame Count:", wf.getnframes())
    print("Compression Type:", wf.getcomptype())  # Should be 'NONE'
    print("Compression Name:", wf.getcompname())  # Should be 'not compressed'