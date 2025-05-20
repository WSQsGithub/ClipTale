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
from src.utils import config as AppConfig

# For mocking async methods
from unittest.mock import AsyncMock


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

    # Create a dummy file to rename
    original_file_path = Path("tests/test_video_test_label.mp4")
    original_file_path.touch() # Create the file

    labeler = ClipLabeler(file_path=original_file_path)
    labeler.add_template("test_video_{label}.mp4")
    labeler.save_label("test_label")
    
    expected_new_path = Path("tests/test_video_test_label.mp4").with_name("test_video_test_label.mp4")
    # This assertion is tricky because the original file is renamed.
    # Let's check if the new file exists and old one doesn't
    # The file is renamed to "test_video_test_label.mp4" based on template and label
    # but the original path was already "tests/test_video_test_label.mp4"
    # So the name doesn't actually change in this specific setup.
    # Let's adjust the initial name to make the test more robust.

    # Setup for a clearer rename test
    initial_file_to_rename = Path("tests/initial_video_for_rename.mp4")
    initial_file_to_rename.touch()
    labeler_for_rename = ClipLabeler(file_path=initial_file_to_rename)
    labeler_for_rename.add_template("renamed_{label}.mp4")
    labeler_for_rename.save_label("final_label")
    
    expected_renamed_path = initial_file_to_rename.with_name("renamed_final_label.mp4")
    assert expected_renamed_path.exists()
    assert not initial_file_to_rename.exists()
    if expected_renamed_path.exists(): # cleanup
        expected_renamed_path.unlink()


    # Test save_label without template
    labeler_no_template = ClipLabeler(file_path=Path("tests/test_video.mp4")) # Use a fresh, existing file
    with pytest.raises(NoTemplateError):
        labeler_no_template.save_label("test_label.mp4") # Original file won't be renamed here

    if original_file_path.exists(): # cleanup from earlier part of test
        original_file_path.unlink()


@pytest.mark.asyncio
@patch('agents.Runner.run') # Patching at the source of call
@patch('src.cliptale.labeler.Transcriber') # Patching at the source of call
async def test_generate_label_with_transcriber_integration(
    mock_transcriber_class: MagicMock,
    mock_runner_run: AsyncMock,
    tmp_path: Path, # pytest fixture for temporary directory
    mocker, # pytest mocker fixture
):
    """
    Tests the integration of Transcriber within ClipLabeler.generate_label.
    """
    # 0. Configure TMP_DIR for this test
    # tmp_path is a pytest fixture providing a Path object to a unique temporary directory
    # We'll use this for our audio extraction path
    # Monkeypatch AppConfig.TMP_DIR to use the pytest tmp_path
    mocker.patch.object(AppConfig, 'TMP_DIR', str(tmp_path))

    # 1. Setup Mocks
    mock_transcriber_instance = mock_transcriber_class.return_value
    mock_transcriber_instance.transcribe.return_value = "mocked transcribed text"

    # Mock the result of Runner.run (which simulates LabelerAgent)
    # Runner.run is an async method
    mock_agent_result = MagicMock()
    mock_agent_result.final_output_as.return_value = "mocked_label"
    mock_runner_run.return_value = mock_agent_result # mock_runner_run itself is already an AsyncMock

    # 2. Instantiate ClipLabeler
    video_file_path = Path("tests/test_video.mp4")
    labeler = ClipLabeler(file_path=video_file_path, duration_limit=Duration_s(1)) # Short duration for speed

    # 3. Mock ffmpeg for audio extraction to avoid actual processing
    #    and ensure audio_path is set correctly within the mocked TMP_DIR.
    #    The key is that labeler.audio_path should be set.
    expected_audio_filename = f"{video_file_path.stem}_start.mp3"
    simulated_audio_path = tmp_path / expected_audio_filename
    
    # We need to ensure extract_audio() sets labeler.audio_path to simulated_audio_path
    # and that this path exists for the transcriber mock.
    # The actual ffmpeg call is mocked, so the file won't be created by ffmpeg.
    # We can touch the file to make it exist.
    
    mock_ffmpeg_output_run = MagicMock(return_value=None) # Simulates ffmpeg.run()
    mock_ffmpeg_output = MagicMock()
    mock_ffmpeg_output.output.return_value = mock_ffmpeg_output_run
    
    mocker.patch("ffmpeg.input", return_value=mock_ffmpeg_output)

    # Call extract_audio
    extracted_audio_path = labeler.extract_audio()

    # Assert that ffmpeg.input().output().run() was called as expected by extract_audio()
    # ffmpeg.input(labeler.file_path, ss=0, t=labeler.duration_limit).output(...).run(...)
    # The path used in output() will be AppConfig.TMP_DIR / f"{base_name}_start.mp3"
    # which is tmp_path / expected_audio_filename
    # So, the first argument to mock_ffmpeg_output.output should be str(simulated_audio_path)
    
    # Check if extract_audio set the audio_path correctly
    assert labeler.audio_path is not None
    assert labeler.audio_path == simulated_audio_path
    assert extracted_audio_path == simulated_audio_path
    
    # For the Transcriber mock to work with `open(self.audio_path, "rb")`, the file needs to exist.
    # The actual Transcriber.transcribe method opens the file. Our mock doesn't, but good practice.
    # In a real scenario, ffmpeg would create this. Here, our ffmpeg mock bypasses file creation.
    # So, we create a dummy file for the sake of the test if the Transcriber wasn't fully mocked
    # or if we were testing a part that reads the file.
    # Since Transcriber is fully mocked, this isn't strictly necessary for *this* test's mocks to pass,
    # but it makes the setup more robust if the Transcriber mock was less comprehensive.
    if not simulated_audio_path.exists():
        simulated_audio_path.touch() # Ensure the file exists

    # 4. Call generate_label
    generated_label = await labeler.generate_label()

    # 5. Assertions
    assert generated_label == "mocked_label"

    # Assert Transcriber was instantiated and its transcribe method called
    mock_transcriber_class.assert_called_once_with()
    mock_transcriber_instance.transcribe.assert_called_once_with(labeler.audio_path)

    # Assert Runner.run was called
    mock_runner_run.assert_called_once()

    # Verify the input argument to Runner.run
    # call_args is a tuple (args, kwargs) or None
    args, kwargs = mock_runner_run.call_args
    assert kwargs['input'] == "mocked transcribed text"
    # We can also check the agent if needed:
    # from src.agents import LabelerAgent
    # assert isinstance(kwargs['starting_agent'], LabelerAgent)

    # 6. Cleanup (tmp_path is handled by pytest)
    # If simulated_audio_path was created, it will be inside tmp_path and cleaned up.
    # No explicit cleanup needed for files in tmp_path due to pytest fixture.
