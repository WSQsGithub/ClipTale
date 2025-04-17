from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.models.errors import AudioFileNotFoundError, NoAudioTranscribedError, UnsupportedAudioFormatError

# write a transcriber agent that transcribes audio files to text using


class Transcriber:
    def __init__(self) -> None:
        self.audio_path: Optional[Path] = None
        self.audio_text: Optional[str] = None
        self.fyi_text: Optional[str] = None
        self.client = OpenAI()

    def transcribe(self, audio_path: Optional[Path] = None, fyi_text: Optional[str] = None) -> str:
        """Transcribe the audio file to text.

        Args:
            audio_path: Path to the audio file to transcribe.

        Returns:
            Transcribed text from the audio file.
        """
        # Placeholder for actual transcription logic
        self.audio_path = audio_path or Path("sample_audio.wav")
        self.fyi_text = fyi_text
        if self.audio_path is None or not self.audio_path.exists():
            raise AudioFileNotFoundError(self.audio_path)
        if self.audio_path is None or self.audio_path.suffix not in [".wav", ".mp3"]:
            raise UnsupportedAudioFormatError(self.audio_path.suffix)

        # Open the audio file
        if self.audio_path is not None:
            with open(self.audio_path, "rb") as audio_file:
                # Call the transcription API
                transcription = self.client.audio.transcriptions.create(model="gpt-4o-transcribe", file=audio_file)

        # Update the audio_text with the transcribed text
        self.audio_text = transcription.text
        return self.audio_text or ""

    @property
    def transcription(
        self,
    ) -> str:
        """Get the transcribed text."""
        if self.audio_text is None:
            raise NoAudioTranscribedError()
        return self.audio_text
