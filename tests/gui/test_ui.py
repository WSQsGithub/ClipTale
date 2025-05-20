import pytest
from unittest.mock import MagicMock, patch, ANY # ANY is useful for some assertions
from pathlib import Path
import ffmpeg # For ffmpeg.Error (assuming this is where it's imported from in the main code)
from concurrent.futures import Future

# Assuming these are the actual paths for the classes used by ClipTaleApp
from src.gui.ui import ClipTaleApp
# ClipLabeler is mocked at 'src.gui.ui.ClipLabeler' as that's where ClipTaleApp imports/uses it
# from src.cliptale.labeler import ClipLabeler # Not needed directly in test if patching 'src.gui.ui.ClipLabeler'

import json # For mocking json.load/dump
from unittest.mock import mock_open

# Import the utility functions to be tested
from src.gui.ui import (
    get_rename_log_path,
    update_rename_log,
    remove_from_rename_log,
    is_file_in_rename_log,
    RENAME_LOG_FILENAME # if needed for asserting path
)

# Helper to create a future that is already resolved
def make_done_future(result=None, exception=None):
    future = Future()
    if exception:
        future.set_exception(exception)
    else:
        future.set_result(result)
    return future

# Test Video Addition and Selection
def test_add_videos_and_selection(app: ClipTaleApp, mocker):
    # Mock askopenfilenames to return a list of mock video file paths
    mock_filepaths_str = ["/fake/video1.mp4", "/fake/video2.avi"]
    mocker.patch('customtkinter.filedialog.askopenfilenames', return_value=mock_filepaths_str)

    # Call app.handle_add_videos()
    app.handle_add_videos()

    # Assert that app.clip_list_view.add_clip_to_list is called for each file
    assert app.clip_list_view.add_clip_to_list.call_count == len(mock_filepaths_str)
    for filepath_str in mock_filepaths_str:
        app.clip_list_view.add_clip_to_list.assert_any_call(Path(filepath_str))
    
    # Assert that control_panel.update_clip_details was called with None (to clear details)
    app.control_panel.update_clip_details.assert_called_with(None)

    # Test app.handle_clip_selection()
    mock_selected_path = Path("/fake/video1.mp4")
    app.handle_clip_selection(mock_selected_path)

    # Assert that app.control_panel.update_clip_details is called
    app.control_panel.update_clip_details.assert_called_with(
        mock_selected_path, 
        status="Ready to generate label", 
        current_label=""
    )
    # Assert that app.clip_labeler_instance is reset (it should be None after selection)
    assert app.clip_labeler_instance is None
    # Assert that actions are enabled
    app.control_panel.enable_actions.assert_called_with(True)

    # Test deselection
    app.handle_clip_selection(None)
    app.control_panel.update_clip_details.assert_called_with(None)
    # After deselection, enable_actions(False) and set_revert_button_state(False) should be called
    app.control_panel.enable_actions.assert_called_with(False)
    app.control_panel.set_revert_button_state.assert_called_with(False) # Added this check based on new logic


# --- Tests for JSON Log Utility Functions ---

@patch('src.gui.ui.Path.home')
def test_get_rename_log_path(mock_home):
    mock_home.return_value = Path("/fake/home")
    expected_path = Path("/fake/home/.cliptale") / RENAME_LOG_FILENAME
    assert get_rename_log_path() == expected_path

@patch('src.gui.ui.get_rename_log_path')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('json.load')
@patch('src.gui.ui.Path.mkdir') # Mock mkdir for parent directory
@patch('src.gui.ui.Path.exists') # Mock Path.exists
def test_update_rename_log(mock_path_exists, mock_mkdir, mock_json_load, mock_json_dump, mock_file_open, mock_get_log_path):
    mock_log_file = Path("/fake/log.json")
    mock_get_log_path.return_value = mock_log_file
    
    original_path = Path("/orig/video.mp4").resolve()
    new_path = Path("/new/video_labeled.mp4").resolve()

    # Case 1: Log file does not exist
    mock_path_exists.return_value = False
    update_rename_log(original_path, new_path)
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file_open.assert_called_with(mock_log_file, "w")
    mock_json_dump.assert_called_with({str(new_path): str(original_path)}, mock_file_open(), indent=4)
    mock_json_load.assert_not_called() # Not called if file doesn't exist

    mock_file_open.reset_mock()
    mock_json_dump.reset_mock()
    mock_mkdir.reset_mock()

    # Case 2: Log file exists and is empty or has other data
    mock_path_exists.return_value = True
    existing_data = {"/some/other.mp4": "/original/other.mp4"}
    mock_json_load.return_value = existing_data.copy() # Return a copy
    
    update_rename_log(original_path, new_path)
    
    mock_file_open.assert_any_call(mock_log_file, "r") # Called for reading
    mock_file_open.assert_any_call(mock_log_file, "w") # Called for writing
    
    expected_data_to_dump = existing_data.copy()
    expected_data_to_dump[str(new_path)] = str(original_path)
    mock_json_dump.assert_called_with(expected_data_to_dump, mock_file_open(), indent=4)
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True) # Still called for parent.mkdir


@patch('src.gui.ui.get_rename_log_path')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('json.load')
@patch('src.gui.ui.Path.exists')
def test_remove_from_rename_log(mock_path_exists, mock_json_load, mock_json_dump, mock_file_open, mock_get_log_path):
    mock_log_file = Path("/fake/log.json")
    mock_get_log_path.return_value = mock_log_file
    
    reverted_new_path = Path("/new/video_labeled.mp4").resolve()
    original_path_val = Path("/orig/video.mp4").resolve()
    
    existing_data = {str(reverted_new_path): str(original_path_val), "/other/new.mp4": "/other/orig.mp4"}

    # Case 1: Entry exists and is removed
    mock_path_exists.return_value = True
    mock_json_load.return_value = existing_data.copy()
    
    result = remove_from_rename_log(reverted_new_path)
    assert result is True
    mock_json_dump.assert_called_with({"/other/new.mp4": "/other/orig.mp4"}, mock_file_open(), indent=4)

    mock_json_dump.reset_mock()

    # Case 2: Entry does not exist
    mock_json_load.return_value = {"/other/new.mp4": "/other/orig.mp4"} # Log without the target entry
    result = remove_from_rename_log(reverted_new_path)
    assert result is False
    mock_json_dump.assert_not_called() # Dump not called if entry wasn't there

    # Case 3: Log file does not exist
    mock_path_exists.return_value = False
    result = remove_from_rename_log(reverted_new_path)
    assert result is False


@patch('src.gui.ui.get_rename_log_path')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
@patch('src.gui.ui.Path.exists')
def test_is_file_in_rename_log(mock_path_exists, mock_json_load, mock_file_open, mock_get_log_path):
    mock_log_file = Path("/fake/log.json")
    mock_get_log_path.return_value = mock_log_file
    
    file_in_log = Path("/new/video_labeled.mp4").resolve()
    file_not_in_log = Path("/another/video.mp4").resolve()
    
    log_data = {str(file_in_log): "/orig/video.mp4"}

    # Case 1: File is in log
    mock_path_exists.return_value = True
    mock_json_load.return_value = log_data
    assert is_file_in_rename_log(file_in_log) is True

    # Case 2: File is not in log
    assert is_file_in_rename_log(file_not_in_log) is False

    # Case 3: Log file does not exist
    mock_path_exists.return_value = False
    assert is_file_in_rename_log(file_in_log) is False

    # Case 4: JSON decode error
    mock_path_exists.return_value = True
    mock_json_load.side_effect = json.JSONDecodeError("err", "doc", 0)
    assert is_file_in_rename_log(file_in_log) is False

# --- End of Tests for JSON Log Utility Functions ---


# --- Tests for ClipTaleApp Functionality ---

@patch('src.gui.ui.update_rename_log') # Mock the logging utility
def test_perform_save_label_logging(mock_update_log, app: ClipTaleApp, mocker):
    # Setup for _perform_save_label
    original_path = Path("/original/video.mp4")
    new_label_text = "new_label"
    expected_new_path = original_path.with_name(f"{new_label_text}{original_path.suffix}")

    # Mock the ClipLabeler instance and its methods
    mock_labeler = MagicMock()
    mock_labeler.file_path = original_path # Set initial path
    # Mock save_label to return the new path and update file_path like the real one
    def mock_save_label_func(label):
        mock_labeler.file_path = original_path.with_name(f"{label}{original_path.suffix}")
        return mock_labeler.file_path
    mock_labeler.save_label.side_effect = mock_save_label_func
    
    app.clip_labeler_instance = mock_labeler

    # Call the method
    returned_new_path = app._perform_save_label(new_label_text)

    # Assertions
    mock_labeler.add_template.assert_called_once_with(f"{{label}}{original_path.suffix}")
    mock_labeler.save_label.assert_called_once_with(label=new_label_text)
    assert returned_new_path == expected_new_path
    
    # Assert that update_rename_log was called correctly
    mock_update_log.assert_called_once_with(original_path.resolve(), expected_new_path.resolve())


@patch('src.gui.ui.remove_from_rename_log') # Mock this utility
@patch('src.gui.ui.Path.rename') # Mock the actual file system rename
@patch('builtins.open', new_callable=mock_open)
@patch('src.gui.ui.get_rename_log_path')
def test_perform_revert_rename_success(mock_get_log_path, mock_open_file, mock_path_rename, mock_remove_log, app: ClipTaleApp, mocker):
    mock_log_file = Path("/fake/home/.cliptale/cliptale_rename_log.json")
    mock_get_log_path.return_value = mock_log_file

    current_renamed_path = Path("/renamed/video_new_label.mp4").resolve()
    original_path = Path("/original/video.mp4").resolve()
    
    mock_log_content = {str(current_renamed_path): str(original_path)}
    # Configure mock_open to simulate reading this log content
    mock_open_file.return_value.read.return_value = json.dumps(mock_log_content)
    
    # Call the method
    reverted_path, new_current_path = app._perform_revert_rename(current_renamed_path)

    # Assertions
    mock_path_rename.assert_called_once_with(original_path) # current_renamed_path.rename(original_path)
    mock_remove_log.assert_called_once_with(current_renamed_path)
    assert reverted_path == current_renamed_path
    assert new_current_path == original_path


@patch('src.gui.ui.get_rename_log_path')
@patch('builtins.open', new_callable=mock_open)
def test_perform_revert_rename_file_not_in_log(mock_open_file, mock_get_log_path, app: ClipTaleApp, mocker):
    mock_log_file = Path("/fake/home/.cliptale/cliptale_rename_log.json")
    mock_get_log_path.return_value = mock_log_file
    
    current_path_not_in_log = Path("/some/other_video.mp4").resolve()
    mock_log_content = {"/renamed/video.mp4": "/original/video.mp4"}
    mock_open_file.return_value.read.return_value = json.dumps(mock_log_content)

    with pytest.raises(FileNotFoundError, match=f"'{current_path_not_in_log.name}' not found in rename log"):
        app._perform_revert_rename(current_path_not_in_log)

@patch('src.gui.ui.get_rename_log_path')
@patch('builtins.open', new_callable=mock_open)
@patch('src.gui.ui.Path.rename')
def test_perform_revert_rename_os_error(mock_path_rename, mock_open_file, mock_get_log_path, app: ClipTaleApp, mocker):
    mock_log_file = Path("/fake/home/.cliptale/cliptale_rename_log.json")
    mock_get_log_path.return_value = mock_log_file

    current_renamed_path = Path("/renamed/video_new_label.mp4").resolve()
    original_path = Path("/original/video.mp4").resolve()
    mock_log_content = {str(current_renamed_path): str(original_path)}
    mock_open_file.return_value.read.return_value = json.dumps(mock_log_content)

    mock_path_rename.side_effect = OSError("Disk full")

    with pytest.raises(OSError, match=f"Failed to revert rename for '{current_renamed_path.name}': Disk full"):
        app._perform_revert_rename(current_renamed_path)


def test_handle_revert_rename_workflow_success(app: ClipTaleApp, mocker):
    mock_current_path = Path("/renamed/video.mp4")
    mock_original_path = Path("/original/video.mp4")
    
    app.clip_list_view.get_selected_clip_path.return_value = mock_current_path
    
    # Mock _perform_revert_rename to simulate success
    mocker.patch.object(app, '_perform_revert_rename', return_value=(mock_current_path, mock_original_path))

    # Call the handler
    app.handle_revert_rename()

    # Assert _perform_revert_rename was called
    app._perform_revert_rename.assert_called_once_with(mock_current_path)

    # Simulate future completion by directly calling the _on_revert_rename_complete method
    app._on_revert_rename_complete(make_done_future(result=(mock_current_path, mock_original_path)))

    # Assertions for GUI updates
    app.clip_list_view.remove_selected_clip_from_list.assert_called_once()
    app.clip_list_view.add_clip_to_list.assert_called_once_with(mock_original_path)
    
    # handle_clip_selection is called after list updates in _on_revert_rename_complete
    # So, the update_clip_details and set_revert_button_state will be called by it.
    # We need to ensure handle_clip_selection was called with the original_path.
    # The conftest mocks clip_list_view, so selection_changed_callback doesn't fire.
    # _on_revert_rename_complete calls handle_clip_selection(original_path)
    # Let's spy on handle_clip_selection to verify it's called.
    spy_handle_clip_selection = mocker.spy(app, 'handle_clip_selection')
    
    # Re-run the completion part that calls handle_clip_selection
    app._on_revert_rename_complete(make_done_future(result=(mock_current_path, mock_original_path)))
    spy_handle_clip_selection.assert_called_with(mock_original_path)
    
    # We can also check the final status message set by _set_ui_busy via control_panel
    # This requires checking the last call to update_clip_details
    # The call order: _on_revert_rename_complete -> handle_clip_selection -> update_clip_details
    #                  _on_revert_rename_complete -> _set_ui_busy -> update_clip_details
    # The _set_ui_busy call is last and sets the "Reverted successfully." message.
    app.control_panel.update_clip_details.assert_called_with(
        mock_original_path, # This path is from the current_selected_path in _set_ui_busy called AFTER handle_clip_selection
        status="Reverted successfully.",
        current_label="" # Assuming handle_clip_selection clears the label
    )


@patch('src.gui.ui.is_file_in_rename_log')
def test_revert_button_state_on_clip_selection(mock_is_in_log, app: ClipTaleApp, mocker):
    mock_path = Path("/fake/video.mp4")

    # Case 1: File is in log
    mock_is_in_log.return_value = True
    app.handle_clip_selection(mock_path)
    app.control_panel.set_revert_button_state.assert_called_with(True)
    mock_is_in_log.assert_called_with(mock_path) # Verify it was called with the path

    # Case 2: File is NOT in log
    mock_is_in_log.return_value = False
    app.handle_clip_selection(mock_path)
    app.control_panel.set_revert_button_state.assert_called_with(False)

    # Case 3: No file selected
    app.handle_clip_selection(None)
    app.control_panel.set_revert_button_state.assert_called_with(False)
    # is_file_in_rename_log should not be called if selected_path is None
    # The mock_is_in_log calls will be 2 from above, not 3.
    assert mock_is_in_log.call_count == 2


# Test "Generate Label" Workflow (Success Case)
def test_generate_label_success(app: ClipTaleApp, mocker):
    mock_video_path = Path("mock_video.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    
    # Mock _perform_full_label_generation to avoid dealing with executor and asyncio.run directly in this unit test
    mocker.patch.object(app, '_perform_full_label_generation', return_value="test_label")

    # Call handle_generate_label
    app.handle_generate_label()

    # Assert that _perform_full_label_generation was called
    app._perform_full_label_generation.assert_called_once_with(mock_video_path)

    # Assert that _set_ui_busy was called to indicate start
    # The exact message can be checked if it's critical, or use ANY
    app.control_panel.update_clip_details.assert_any_call(
        mock_video_path, status="Initializing label generation...", current_label=""
    )
    
    # Directly call the completion handler with a successful future
    # This simulates the self.after scheduling and future completion
    app._on_label_generation_complete(make_done_future(result="test_label"))

    # Assertions for success
    app.control_panel.set_current_label.assert_called_once_with("test_label")
    
    # Check status update for success
    # The update_clip_details is called by _set_ui_busy(False, status_message=...)
    # We need to check the *last* call to update_clip_details related to status.
    # The _set_ui_busy calls update_clip_details.
    # The final status message is "Label generated successfully."
    app.control_panel.update_clip_details.assert_called_with(
        mock_video_path, 
        status="Label generated successfully.", 
        current_label="test_label" # Assuming get_current_label returns this after set_current_label
    )
    
    # Check that action buttons on app.control_panel are re-enabled
    # This is part of _set_ui_busy(False, ...)
    # enable_actions(True) should be called if a clip is selected
    app.control_panel.enable_file_operations.assert_called_with(True)
    app.control_panel.enable_actions.assert_called_with(True)


# Test "Generate Label" Workflow (ffmpeg Error Case)
def test_generate_label_ffmpeg_error(app: ClipTaleApp, mocker):
    mock_video_path = Path("mock_video.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    
    # Mock _perform_full_label_generation to raise ffmpeg.Error
    # Note: ffmpeg.Error typically takes (cmd, stdout, stderr)
    # For testing, a simple message might suffice if the error formatting logic handles it.
    # The main code uses e.stderr.decode() or str(e).
    mock_ffmpeg_error = ffmpeg.Error(cmd="test", stdout=b"", stderr=b"ffmpeg failed")
    mocker.patch.object(app, '_perform_full_label_generation', side_effect=mock_ffmpeg_error)

    # Call handle_generate_label
    app.handle_generate_label()

    # Assert _perform_full_label_generation was called
    app._perform_full_label_generation.assert_called_once_with(mock_video_path)
    
    # Directly call the completion handler with a future containing the exception
    app._on_label_generation_complete(make_done_future(exception=mock_ffmpeg_error))

    # Assertions for error case
    # app.control_panel.set_current_label should not have been called with a new label.
    # It might be called with "" initially, so check no *other* calls.
    # If it was called with "" in handle_generate_label, that's one call.
    app.control_panel.set_current_label.assert_called_once_with("") # Called at the start of handle_generate_label

    # Status label on app.control_panel shows an error message
    # The final status message is "Audio extraction failed: ffmpeg failed"
    app.control_panel.update_clip_details.assert_called_with(
        mock_video_path, 
        status="Audio extraction failed: ffmpeg failed", 
        current_label="" # Label was cleared and not set
    )
    
    # Action buttons are re-enabled
    app.control_panel.enable_file_operations.assert_called_with(True)
    app.control_panel.enable_actions.assert_called_with(True)

# TODO: Add tests for TranscriptionAuthError and TranscriptionConnectionError
# TODO: Add tests for save label success and failure cases.
# TODO: Add test for handle_remove_selected_video

def test_generate_label_transcription_auth_error(app: ClipTaleApp, mocker):
    from src.models.errors import TranscriptionAuthError # Import here for clarity
    mock_video_path = Path("mock_video.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    
    mock_auth_error = TranscriptionAuthError("Custom auth error message.")
    mocker.patch.object(app, '_perform_full_label_generation', side_effect=mock_auth_error)

    app.handle_generate_label()
    app._perform_full_label_generation.assert_called_once_with(mock_video_path)
    
    app._on_label_generation_complete(make_done_future(exception=mock_auth_error))
    
    app.control_panel.set_current_label.assert_called_once_with("")
    app.control_panel.update_clip_details.assert_called_with(
        mock_video_path, 
        status="Custom auth error message.", 
        current_label=""
    )
    app.control_panel.enable_file_operations.assert_called_with(True)
    app.control_panel.enable_actions.assert_called_with(True)


def test_generate_label_transcription_connection_error(app: ClipTaleApp, mocker):
    from src.models.errors import TranscriptionConnectionError # Import here
    mock_video_path = Path("mock_video.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    
    mock_conn_error = TranscriptionConnectionError("Custom connection error.")
    mocker.patch.object(app, '_perform_full_label_generation', side_effect=mock_conn_error)

    app.handle_generate_label()
    app._perform_full_label_generation.assert_called_once_with(mock_video_path)
    
    app._on_label_generation_complete(make_done_future(exception=mock_conn_error))
    
    app.control_panel.set_current_label.assert_called_once_with("")
    app.control_panel.update_clip_details.assert_called_with(
        mock_video_path, 
        status="Custom connection error.", 
        current_label=""
    )
    app.control_panel.enable_file_operations.assert_called_with(True)
    app.control_panel.enable_actions.assert_called_with(True)

def test_save_label_success(app: ClipTaleApp, mocker):
    mock_video_path = Path("mock_video.mp4")
    new_video_path = Path("new_label.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    app.control_panel.get_current_label.return_value = "new_label" # User typed or generated label

    # Mock the ClipLabeler instance that would have been created by generate_label
    mock_labeler_instance = MagicMock()
    app.clip_labeler_instance = mock_labeler_instance # Pre-set the instance

    mocker.patch.object(app, '_perform_save_label', return_value=new_video_path)

    app.handle_save_label()

    app._perform_save_label.assert_called_once_with("new_label")
    
    # Simulate future completion
    app._on_save_label_complete(make_done_future(result=new_video_path), old_path=mock_video_path)

    app.clip_list_view.remove_selected_clip_from_list.assert_called_once()
    app.clip_list_view.add_clip_to_list.assert_called_once_with(new_video_path)
    app.control_panel.update_clip_details.assert_called_with(
        new_video_path, 
        status="Label saved", 
        current_label="new_label"
    )
    app.control_panel.enable_file_operations.assert_called_with(True)
    app.control_panel.enable_actions.assert_called_with(True)


def test_save_label_failure_empty_label(app: ClipTaleApp, mocker):
    mock_video_path = Path("mock_video.mp4")
    app.clip_list_view.get_selected_clip_path.return_value = mock_video_path
    app.control_panel.get_current_label.return_value = "   " # Empty/whitespace label
    app.clip_labeler_instance = MagicMock() # Assume labeler was initialized

    # Spy on _perform_save_label to ensure it's NOT called
    spy_perform_save = mocker.spy(app, '_perform_save_label')

    app.handle_save_label()

    spy_perform_save.assert_not_called()
    app.control_panel.update_clip_details.assert_called_with(
        mock_video_path, 
        status="Error: Label cannot be empty.", 
        current_label=""
    )
    # Buttons should remain in a state consistent with a selected clip, as no long op started
    app.control_panel.enable_actions.assert_called_with(True) # Assuming it was true before


def test_handle_remove_selected_video(app: ClipTaleApp, mocker):
    app.handle_remove_selected_video()
    app.clip_list_view.remove_selected_clip_from_list.assert_called_once()
    assert app.clip_labeler_instance is None # Ensure instance is cleared
    # Further checks on control_panel state (e.g. update_clip_details(None))
    # would happen if the callback from ClipListView -> handle_clip_selection is triggered.
    # For this direct test, we only check what handle_remove_selected_video itself does.
    # If ClipListView's callback is mocked, we'd need to simulate that call too.
    # The conftest.py mocks ClipListView, so its callback won't fire automatically.
    # We can assume handle_clip_selection(None) will be tested separately or its effects
    # (like calling control_panel.update_clip_details(None)) are asserted there.
    # Here, we primarily test the direct actions of handle_remove_selected_video.
    # If the selection callback is part of the contract, then:
    # app.clip_list_view.selection_changed_callback(None) # This is what would happen
    # And then assert the effects of handle_clip_selection(None)
    app.control_panel.update_clip_details.assert_called_with(None)
    app.control_panel.enable_actions.assert_called_with(False)
