import unittest
from pathlib import Path

from src.agents.transcriber import Transcriber


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        self.transcriber = Transcriber()

    def test_transcribe_valid_file(self):
        # Assuming 'sample_audio.mp3' is a valid file in the test directory
        audio_path = Path("tests/sample_audio.mp3")
        self.transcriber.transcribe(audio_path)
        self.assertIsNotNone(self.transcriber.audio_text)

    def test_transcribe_missing_file(self):
        audio_path = Path("tests/missing_audio.mp3")
        with self.assertRaises(FileNotFoundError):
            self.transcriber.transcribe(audio_path)

    def test_transcribe_unsupported_format(self):
        audio_path = Path("tests/sample_audio.txt")
        with self.assertRaises(ValueError):
            self.transcriber.transcribe(audio_path)

    def test_transcription_before_transcribe(self):
        with self.assertRaises(ValueError):
            _ = self.transcriber.transcription


if __name__ == "__main__":
    unittest.main()
