class AgentCallError(Exception):
    message = "Error calling agent: {error_message}"


class ClipLabelerError(Exception):
    """Base exception class for ClipLabeler errors."""

    pass


class VideoExtensionNotSupportedError(ClipLabelerError, ValueError):
    message = "Video extension not supported: {file_extension}, supported formats are: {supported_formats}"


class VideoFileNotFoundError(ClipLabelerError, FileNotFoundError):
    message = "Video file not found: {file_path}"


class InvalidDurationError(ClipLabelerError, ValueError):
    message = "Duration limit must be positive"


class InvalidTemplateError(ClipLabelerError, ValueError):
    message = "Template must contain '{label}' placeholder"


class NoTemplateError(ClipLabelerError, ValueError):
    message = "No rename template set - call add_template() first"


class AudioFileNotFoundError(ClipLabelerError, FileNotFoundError):
    message = "Audio file not found for video: {file_path}"
