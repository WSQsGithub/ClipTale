from pathlib import Path

import pytest

from src.agents.transcriber import Transcriber


@pytest.fixture
def transcriber():
    return Transcriber()


def test_transcribe_valid_file(transcriber):
    # Assuming 'sample_audio.wav' is a valid file in the test directory
    audio_path = Path("tests/sample_audio.wav")
    transcriber.transcribe(audio_path)
    assert transcriber.audio_text is not None


def test_transcribe_missing_file(transcriber):
    audio_path = Path("tests/missing_audio.mp3")
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe(audio_path)


def test_transcribe_unsupported_format(transcriber):
    audio_path = Path("tests/sample_audio.txt")
    with pytest.raises(ValueError):
        transcriber.transcribe(audio_path)


def test_transcription_before_transcribe(transcriber):
    with pytest.raises(ValueError):
        _ = transcriber.transcription
