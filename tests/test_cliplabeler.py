from pathlib import Path
from unittest.mock import MagicMock, patch

import ffmpeg
import pytest

from src.cliptale.labeler import ClipLabeler, Duration_s
from src.models.errors import (
    AudioFileNotFoundError,
    InvalidDurationError,
    InvalidTemplateError,
    NoTemplateError,
    VideoExtensionNotSupportedError,
    VideoFileNotFoundError,
)


def test_cliplabeler_initialization():
    # Test initialization with valid file path and duration
    valid_path = Path("tests/test_video.mp4")
    labeler = ClipLabeler(file_path=valid_path, duration_limit=Duration_s(10))
    assert labeler.file_path == valid_path
    assert labeler.duration_limit == 10

    # Test initialization with invalid file path
    invalid_path = Path("test/non_existent_video.mp4")
    with pytest.raises(VideoFileNotFoundError):
        ClipLabeler(file_path=invalid_path)

    # Test initialization with unsupported video extension
    unsupported_path = Path("tests/sample_audio.txt")
    with pytest.raises(VideoExtensionNotSupportedError):
        ClipLabeler(file_path=unsupported_path)

    # Test initialization with invalid duration
    with pytest.raises(InvalidDurationError):
        ClipLabeler(file_path=valid_path, duration_limit=Duration_s(-5))


def test_add_template():
    labeler = ClipLabeler(file_path=Path("tests/test_video.mp4"))
    valid_template = "{filename}_{label}.mp4"
    labeler.add_template(valid_template)
    assert labeler.rename_template == valid_template

    invalid_template = "video_label.mp4"
    with pytest.raises(InvalidTemplateError):
        labeler.add_template(invalid_template)


def test_extract_audio():
    labeler = ClipLabeler(file_path=Path("tests/test_video.mp4"))
    with patch("ffmpeg.input") as mock_input:
        mock_output = MagicMock()
        mock_input.return_value.output.return_value = mock_output
        mock_output.run.return_value = None

        audio_path = labeler.extract_audio()
        assert audio_path is not None
        assert audio_path.name == "test_video_start.mp3"

    # Test ffmpeg error handling
    with patch("ffmpeg.input", side_effect=ffmpeg.Error("ffmpeg error", b"", b"")):  # noqa: SIM117
        with pytest.raises(ffmpeg.Error):
            labeler.extract_audio()


@pytest.mark.asyncio
async def test_generate_label():
    labeler = ClipLabeler(file_path=Path("tests/test_video.mp4"))
    labeler.audio_text = "sample audio text"

    with patch("src.cliptale.labeler.Runner.run", return_value=MagicMock(final_output_as=lambda x: "label")):
        label = await labeler.generate_label()
        assert label == "label"

    # Test AudioFileNotFoundError
    labeler.audio_text = None
    with pytest.raises(AudioFileNotFoundError):
        await labeler.generate_label()


def test_save_label():
    labeler = ClipLabeler(file_path=Path("tests/test_video.mp4"))
    labeler.add_template("test_video_{label}.mp4")

    labeler.save_label("test_label")

    # Test save_label without template
    labeler = ClipLabeler(file_path=Path("tests/test_video_test_label.mp4"))
    with pytest.raises(NoTemplateError):
        labeler.save_label("test_label.mp4")
