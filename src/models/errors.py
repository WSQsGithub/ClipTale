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
    def __init__(self, file_path):
        self.message = f"Audio file not found: {file_path}"
        super().__init__(self.message)


class UnsupportedAudioFormatError(ClipLabelerError, ValueError):
    def __init__(self, file_suffix):
        self.message = f"Unsupported audio format: {file_suffix}. Supported formats are .wav and .mp3."
        super().__init__(self.message)


class NoAudioTranscribedError(ClipLabelerError, ValueError):
    def __init__(self):
        self.message = "No audio file has been transcribed yet."
        super().__init__(self.message)
