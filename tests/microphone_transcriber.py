import wave
from pathlib import Path

import pyaudio
from openai import OpenAI


class Transcriber:
    def __init__(self):
        self.audio_path = None
        self.audio_text = None

    def transcribe(self, audio_path: Path) -> str:
        """Transcribe the audio file to text."""
        self.audio_path = audio_path
        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")  # noqa: TRY003
        if self.audio_path.suffix not in [".wav", ".mp3"]:
            print(f"Unsupported audio format: {self.audio_path.suffix}. Supported formats are .wav and .mp3.")

        # Initialize OpenAI client
        client = OpenAI()

        # Open the audio file
        with open(self.audio_path, "rb") as audio_file:
            # Call the transcription API
            transcription = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=audio_file)

        # Update the audio_text with the transcribed text
        self.audio_text = transcription.text
        return self.audio_text


def record_audio(output_path: str, duration: int = 5):
    """Record audio from the microphone and save it to a file."""
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 44100  # Record at 44100 samples per second
    p = pyaudio.PyAudio()

    print("Recording...")

    stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True)

    frames = []

    for _ in range(0, int(fs / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Recording finished.")

    wf = wave.open(output_path, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b"".join(frames))
    wf.close()


def main():
    audio_file = "microphone_audio.wav"
    record_audio(audio_file, duration=5)

    transcriber = Transcriber()
    transcribed_text = transcriber.transcribe(Path(audio_file))
    print("Transcribed Text:", transcribed_text)


if __name__ == "__main__":
    main()
