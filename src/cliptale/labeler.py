from pathlib import Path
from typing import NewType, Optional

import ffmpeg

from agents import Runner
from src.agents import LabelerAgent
from src.models.errors import (
    AgentCallError,
    AudioFileNotFoundError,
    InvalidDurationError,
    InvalidTemplateError,
    NoTemplateError,
    VideoExtensionNotSupportedError,
    VideoFileNotFoundError,
)
from src.utils.config import (
    TMP_DIR,
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
        self.audio_path: Optional[Path] = None
        self.audio_text: Optional[str] = None
        self.labeler_agent = LabelerAgent()

    def add_template(self, template: str) -> None:
        """Set the template string for renaming labeled files.

        Args:
            template: String template containing {label} placeholder
        """
        if "{label}" not in template:
            raise InvalidTemplateError(InvalidTemplateError.message)
        self.rename_template = template

    def extract_audio(self) -> Optional[Path]:
        """Extract audio segments from start and end of video.

        Extracts the first self.duration_limit seconds of audio.
        """
        base_name = self.file_path.stem
        start_audio_path = Path(TMP_DIR) / f"{base_name}_start.mp3"
        try:
            ffmpeg.input(self.file_path, ss=0, t=self.duration_limit).output(
                start_audio_path, acodec="mp3", audio_bitrate="192k"
            ).run(overwrite_output=True)
        except ffmpeg.Error as e:
            raise ffmpeg.Error(f"Failed to extract audio: {e.stderr.decode()}", stdout=e.stdout, stderr=e.stderr) from e  # noqa: TRY003
        else:
            self.audio_path = start_audio_path
            return start_audio_path

    async def generate_label(self) -> Optional[str]:
        """Generate a label by analyzing the extracted audio segment's text content.

        Returns:
            Generated label string
        """
        # pass the audio to the model and generate a label
        if not self.audio_text:
            raise AudioFileNotFoundError(AudioFileNotFoundError.message.format(file_path=self.file_path))
        try:  # TODO: agent does not support audio files yet, have to use text
            agent_input = self.audio_text
            result = await Runner.run(starting_agent=self.labeler_agent, input=agent_input)
        except Exception as e:
            raise AgentCallError(AgentCallError.message.format(error_message=str(e))) from e
        else:
            return result.final_output_as(str)

    def save_label(self, label: Optional[str]) -> None:
        """Save the generated label to file.

        Args:
            label: The label string to save
        """
        if not self.rename_template:
            raise NoTemplateError(NoTemplateError.message)
        if not label:
            label = self.file_path.stem
        pass
