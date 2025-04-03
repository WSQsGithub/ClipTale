from pathlib import Path
from typing import NewType, Optional

from src.models.errors import (
    InvalidDurationError,
    InvalidTemplateError,
    NoTemplateError,
    VideoExtensionNotSupportedError,
    VideoFileNotFoundError,
)

# Type alias for duration in seconds to improve type safety and readability
Duration_s = NewType("Duration_s", int)

# Default duration limit for clip analysis (in seconds)
DEFAULT_DURATION_LIMIT = Duration_s(15)


class ClipLabeler:
    """A class for labeling video clips by analyzing their audio content.

    Attributes:
        file_path: Path to the video file
        rename_template: Optional template string for renaming labeled files
        duration_limit: Maximum duration in seconds to analyze from start/end of clip
    """

    SUPPORTED_VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")

    def __init__(self, file_path: Path, duration_limit: Duration_s = DEFAULT_DURATION_LIMIT) -> None:
        """Initialize ClipLabeler with video file path and analysis duration limit.

        Args:
            file_path: Path to the video file to analyze
            duration_limit: Maximum duration in seconds to analyze from start/end of clip.
                            Defaults to 15 seconds.
        """
        if not file_path.exists():
            raise VideoFileNotFoundError(VideoFileNotFoundError.message.format(file_path=file_path))
        if file_path.suffix not in self.SUPPORTED_VIDEO_EXTENSIONS:
            raise VideoExtensionNotSupportedError(
                VideoFileNotFoundError.message.format(
                    file_path=file_path, supported_formats=self.SUPPORTED_VIDEO_EXTENSIONS
                )
            )
        if duration_limit <= 0:
            raise InvalidDurationError(InvalidDurationError.message)

        self.file_path = file_path
        self.rename_template: Optional[str] = None
        self.duration_limit: Duration_s = duration_limit
        self.video = None

    def add_template(self, template: str) -> None:
        """Set the template string for renaming labeled files.

        Args:
            template: String template containing {label} placeholder
        """
        if "{label}" not in template:
            raise InvalidTemplateError(InvalidTemplateError.message)
        self.rename_template = template

    def read_video(self) -> None:
        """Read and validate the video file."""
        # Placeholder for video reading logic
        pass

    def extract_audio(self) -> None:
        """Extract audio segments from start and end of video.

        Extracts the first and last self.duration_limit seconds of audio.
        """
        pass

    def generate_label(self) -> str:
        """Generate a label by analyzing the extracted audio segments.

        Returns:
            Generated label string
        """
        # pass the audio to the model and generate a label
        return ""

    def save_label(self, label: str) -> None:
        """Save the generated label to file.

        Args:
            label: The label string to save
        """
        if not self.rename_template:
            raise NoTemplateError(NoTemplateError.message)
        # Placeholder for saving label logic
        pass
