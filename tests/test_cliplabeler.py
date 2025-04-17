from pathlib import Path

import pytest

from src.cliptale.labeler import ClipLabeler, Duration_s
from src.models.errors import (
    InvalidDurationError,
    InvalidTemplateError,
    NoTemplateError,
    VideoExtensionNotSupportedError,
    VideoFileNotFoundError,
)


def test_cliplabeler_initialization():
    # Test initialization with valid file path and duration
    valid_path = Path("test_video.mp4")
    labeler = ClipLabeler(file_path=valid_path, duration_limit=Duration_s(10))
    assert labeler.file_path == valid_path
    assert labeler.duration_limit == 10

    # Test initialization with invalid file path
    invalid_path = Path("non_existent_video.mp4")
    with pytest.raises(VideoFileNotFoundError):
        ClipLabeler(file_path=invalid_path)

    # Test initialization with unsupported video extension
    unsupported_path = Path("video.txt")
    with pytest.raises(VideoExtensionNotSupportedError):
        ClipLabeler(file_path=unsupported_path)

    # Test initialization with invalid duration
    with pytest.raises(InvalidDurationError):
        ClipLabeler(file_path=valid_path, duration_limit=Duration_s(-5))


def test_add_template():
    labeler = ClipLabeler(file_path=Path("test_video.mp4"))
    valid_template = "video_{label}.mp4"
    labeler.add_template(valid_template)
    assert labeler.rename_template == valid_template

    invalid_template = "video_label.mp4"
    with pytest.raises(InvalidTemplateError):
        labeler.add_template(invalid_template)


def test_save_label():
    labeler = ClipLabeler(file_path=Path("test_video.mp4"))
    labeler.add_template("video_{label}.mp4")
    labeler.save_label("test_label")
    assert labeler.file_path.name == "video_test_label.mp4"

    # Test save_label without template
    labeler = ClipLabeler(file_path=Path("test_video.mp4"))
    with pytest.raises(NoTemplateError):
        labeler.save_label("test_label")
