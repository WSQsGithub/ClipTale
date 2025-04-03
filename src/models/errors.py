class ClipLabelerError(Exception):
    """Base exception class for ClipLabeler errors."""

    pass


class VideoFormatNotSupportedError(ClipLabelerError, ValueError):
    message = "Video format not supported: {file_extension}, supported formats are: {supported_formats}"


class VideoFileNotFoundError(ClipLabelerError, FileNotFoundError):
    message = "Video file not found: {file_path}"


class InvalidDurationError(ClipLabelerError, ValueError):
    message = "Duration limit must be positive"


class InvalidTemplateError(ClipLabelerError, ValueError):
    message = "Template must contain '{label}' placeholder"


class NoTemplateError(ClipLabelerError, ValueError):
    message = "No rename template set - call add_template() first"
