import cProfile
import customtkinter as ctk
import threading

from .splash_screen import show_splash_screen
from .clip_list_view import ClipListView
from .control_panel import ControlPanel

# For file dialogs and path handling
from customtkinter.filedialog import askopenfilenames
from pathlib import Path
from typing import Optional # For type hinting

# To get supported video extensions and for ClipLabeler functionality
from src.cliptale.labeler import ClipLabeler, VideoFileNotFoundError, AudioFileNotFoundError, AgentCallError
from src.models.errors import TranscriptionAuthError, TranscriptionConnectionError # Import new custom errors
import ffmpeg # For ffmpeg.Error

# For non-blocking operations
import asyncio
from typing import Callable, Dict # For _check_future_status type hint and Dict for log
from concurrent.futures import ThreadPoolExecutor, Future
import json # For logging renames


# --- JSON Logging Utilities for File Renames ---
RENAME_LOG_FILENAME = "cliptale_rename_log.json"

def get_rename_log_path() -> Path:
    """Returns the path to the rename log file."""
    # .cliptale directory in user's home
    app_dir = Path.home() / ".cliptale"
    return app_dir / RENAME_LOG_FILENAME

def update_rename_log(original_path: Path, new_path: Path):
    """Updates the JSON log file with a new rename operation."""
    log_file_path = get_rename_log_path()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    log_data: Dict[str, str] = {}
    if log_file_path.exists():
        try:
            with open(log_file_path, "r") as f:
                log_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading rename log file {log_file_path}: {e}")
            # Decide if we want to overwrite or stop. For now, start fresh if corrupt.
            log_data = {} 
    
    # Log new path as key, original path as value (both as strings)
    log_data[str(new_path)] = str(original_path)

    try:
        with open(log_file_path, "w") as f:
            json.dump(log_data, f, indent=4)
    except IOError as e:
        print(f"Error writing to rename log file {log_file_path}: {e}")

def remove_from_rename_log(reverted_new_path: Path) -> bool:
    """Removes an entry from the rename log.
    
    Args:
        reverted_new_path: The path that was reverted (this was the 'new_path' in the log).
    
    Returns:
        True if the entry was successfully removed, False otherwise.
    """
    log_file_path = get_rename_log_path()
    if not log_file_path.exists():
        print(f"Rename log file not found: {log_file_path}")
        return False

    log_data: Dict[str, str] = {}
    try:
        with open(log_file_path, "r") as f:
            log_data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading rename log file {log_file_path} for removal: {e}")
        return False

    reverted_new_path_str = str(reverted_new_path.resolve())
    if reverted_new_path_str in log_data:
        del log_data[reverted_new_path_str]
        try:
            with open(log_file_path, "w") as f:
                json.dump(log_data, f, indent=4)
            print(f"Removed '{reverted_new_path_str}' from rename log.")
            return True
        except IOError as e:
            print(f"Error writing updated rename log file {log_file_path}: {e}")
            return False
    else:
        print(f"Path '{reverted_new_path_str}' not found in rename log for removal.")
        return False

def is_file_in_rename_log(file_path: Path) -> bool:
    """Checks if the given file_path (as a string key) exists in the rename log."""
    log_file_path = get_rename_log_path()
    if not log_file_path.exists():
        return False

    try:
        with open(log_file_path, "r") as f:
            log_data: Dict[str, str] = json.load(f)
        # The log stores new_path (renamed file) as key.
        return str(file_path.resolve()) in log_data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading rename log file {log_file_path} for checking: {e}")
        return False


class ClipTaleApp(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title("ClipTale v0.1.0")
        self.geometry("1200x720") # Adjusted default size

        # Configure main window grid layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) # Left panel, adjustable
        self.grid_columnconfigure(1, weight=3) # Right panel, takes more space

        # Left Panel Frame (for ClipListView)
        self.left_panel_frame = ctk.CTkFrame(self, width=300) # Initial width, can be adjusted by grid weight
        self.left_panel_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.left_panel_frame.grid_rowconfigure(0, weight=1) # Make sure content within can expand
        self.left_panel_frame.grid_columnconfigure(0, weight=1)

        # Right Panel Frame (for ControlPanel)
        self.right_panel_frame = ctk.CTkFrame(self)
        self.right_panel_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.right_panel_frame.grid_rowconfigure(0, weight=1) # Make sure content within can expand
        self.right_panel_frame.grid_columnconfigure(0, weight=1)

        # Instantiate and place ClipListView
        self.clip_list_view = ClipListView(master=self.left_panel_frame)
        self.clip_list_view.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Instantiate and place ControlPanel
        self.control_panel = ControlPanel(master=self.right_panel_frame)
        self.control_panel.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # --- Connect UI component signals/callbacks ---
        # Connect "Add Video(s)" button from ControlPanel to handler method
        self.control_panel.add_videos_button.configure(command=self.handle_add_videos)
        
        # Set the callback for selection changes in ClipListView
        self.clip_list_view.selection_changed_callback = self.handle_clip_selection
        
        # Connect "Remove Selected" button from ControlPanel to handler method
        self.control_panel.remove_selected_button.configure(command=self.handle_remove_selected_video)

        # Connect "Generate Label" and "Save Label" buttons
        self.control_panel.generate_label_button.configure(command=self.handle_generate_label)
        self.control_panel.save_label_button.configure(command=self.handle_save_label)
        # Connect "Revert Rename" button
        self.control_panel.revert_rename_button.configure(command=self.handle_revert_rename)


        # Store supported formats (though ClipLabeler handles this internally)
        self.supported_formats = ClipLabeler.SUPPORTED_VIDEO_EXTENSIONS
        
        # For running blocking tasks in separate threads
        self.executor = ThreadPoolExecutor(max_workers=2) # One for ffmpeg, one for API/save
        
        # Instance of ClipLabeler for the currently selected clip
        self.clip_labeler_instance: Optional[ClipLabeler] = None


    def handle_add_videos(self):
        # Prepare filetypes for the dialog
        filetypes = []
        # Use self.supported_formats if needed, or let ClipLabeler define them
        if self.supported_formats:
            filetypes = [(f"{ext.upper()[1:]} files", f"*{ext}") for ext in self.supported_formats]
            filetypes.append(("All files", "*.*"))
        else:
            filetypes.append(("All files", "*.*"))

        filepaths = askopenfilenames(
            title="Select Video Files",
            filetypes=filetypes
        )
        
        if filepaths: # User selected files
            for filepath_str in filepaths:
                video_path = Path(filepath_str)
                self.clip_list_view.add_clip_to_list(video_path)
            # Optionally, select the first added clip or clear selection
            self.control_panel.update_clip_details(None) # Clear details or update for first added

    def handle_clip_selection(self, selected_path: Optional[Path]):
        self.clip_labeler_instance = None # Reset labeler instance for new selection
        if selected_path:
            self.control_panel.update_clip_details(selected_path, status="Ready to generate label", current_label="")
            self.control_panel.enable_actions(True) # Enable Generate/Save
            # Dynamically set revert button state based on log
            can_revert = is_file_in_rename_log(selected_path)
            self.control_panel.set_revert_button_state(can_revert)
        else:
            self.control_panel.update_clip_details(None)
            self.control_panel.enable_actions(False) # Disable Generate/Save
            self.control_panel.set_revert_button_state(False) # Disable Revert

    def handle_remove_selected_video(self):
        self.clip_list_view.remove_selected_clip_from_list()
        # The selection_changed_callback in ClipListView should call handle_clip_selection(None)
        # which then updates the control panel and disables actions.
        # So, no explicit call to self.control_panel.update_clip_details(None) here is needed.
        self.clip_labeler_instance = None # Clear instance if removed clip was selected

    def _set_ui_busy(self, busy: bool, status_message: str = ""):
        if busy:
            self.control_panel.enable_file_operations(False)
            self.control_panel.enable_actions(False) # Disables Generate/Save
            self.control_panel.set_revert_button_state(False) # Also disable Revert when busy
            if status_message:
                # Assuming status_value is the correct label in ControlPanel
                current_path = self.clip_list_view.get_selected_clip_path()
                self.control_panel.update_clip_details(
                    current_path, # Keep other details if path exists
                    status=status_message, 
                    current_label=self.control_panel.get_current_label() if current_path else ""
                )
        else:
            self.control_panel.enable_file_operations(True)
            # When not busy, enable_actions handles Generate/Save.
            # Revert button state is determined by handle_clip_selection, which should be called
            # after an operation if the selection might have changed or its log status changed.
            current_selected_path = self.clip_list_view.get_selected_clip_path()
            if current_selected_path:
                self.control_panel.enable_actions(True) # Enable Generate/Save
                can_revert = is_file_in_rename_log(current_selected_path)
                self.control_panel.set_revert_button_state(can_revert)
            else:
                self.control_panel.enable_actions(False) # Disable Generate/Save
                self.control_panel.set_revert_button_state(False) # Disable Revert
            
            if status_message: # Update status on completion too
                current_path = current_selected_path # Use the path we just got
                self.control_panel.update_clip_details(
                    current_path, 
                    status=status_message, 
                    current_label=self.control_panel.get_current_label() if current_path else ""
                )


    def _perform_full_label_generation(self, selected_path: Path) -> str:
        """
        Synchronous wrapper for the entire label generation process (extract + generate).
        This will be run in a thread by the executor.
        """
        self.clip_labeler_instance = ClipLabeler(file_path=selected_path)
        
        # 1. Audio Extraction (blocking I/O)
        # No need to update GUI from here, _set_ui_busy handles initial status
        self.clip_labeler_instance.extract_audio() # This can raise ffmpeg.Error
        
        # 2. Label Generation (async, run within this thread using asyncio.run)
        # No need to update GUI from here
        generated_label = asyncio.run(self.clip_labeler_instance.generate_label()) # This can raise AgentCallError
        return generated_label


    def _on_label_generation_complete(self, future: Future):
        try:
            generated_label = future.result() # Get result from the future
            self.control_panel.set_current_label(generated_label)
            self._set_ui_busy(False, status_message="Label generated successfully.")
        except ffmpeg.Error as e:
            error_msg = f"Audio extraction failed: {e.stderr.decode() if e.stderr else str(e)}"
            self._set_ui_busy(False, status_message=error_msg)
            # Optionally show a dialog: ctk.CTkMessagebox(title="Error", message=error_msg)
        except TranscriptionAuthError as e: # Catch specific auth error
            self._set_ui_busy(False, status_message=str(e))
        except TranscriptionConnectionError as e: # Catch specific connection error
            self._set_ui_busy(False, status_message=str(e))
        except AgentCallError as e: # This might catch re-raised errors if Transcriber's errors are wrapped by AgentCallError
            self._set_ui_busy(False, status_message=f"Label generation process error: {e}")
        except Exception as e: # Catch-all for other unexpected errors
            self._set_ui_busy(False, status_message=f"An unexpected error occurred during label generation: {e}")


    def handle_generate_label(self):
        selected_path = self.clip_list_view.get_selected_clip_path()
        if not selected_path:
            # TODO: Show proper error (e.g., CTkMessagebox or update status label)
            print("No clip selected for generating label.")
            self.control_panel.update_clip_details(None, status="Error: No clip selected.")
            return

        self._set_ui_busy(True, status_message="Initializing label generation...")
        self.control_panel.set_current_label("") # Clear previous label

        # Offload the entire blocking + async chain to the executor
        future = self.executor.submit(self._perform_full_label_generation, selected_path)
        
        # Periodically check the future's status from the main Tkinter thread
        self.after(100, lambda: self._check_future_status(future, self._on_label_generation_complete))


    def _perform_save_label(self, current_label_text: str) -> Path:
        """
        Synchronous wrapper for saving the label.
        This will be run in a thread by the executor.
        """
        if not self.clip_labeler_instance or not self.clip_labeler_instance.file_path:
            raise ValueError("ClipLabeler instance not available or file path missing.")

        original_absolute_path = self.clip_labeler_instance.file_path.resolve()
        template = f"{{label}}{original_absolute_path.suffix}"
        self.clip_labeler_instance.add_template(template)
        
        # save_label returns the new_path (absolute if file_path was absolute)
        new_path_result = self.clip_labeler_instance.save_label(label=current_label_text)
        
        # Log the rename operation
        # Ensure new_path_result is also absolute for consistency, though save_label should handle this.
        update_rename_log(original_absolute_path, new_path_result.resolve())
        
        return new_path_result # Return the new path (already updated in instance)


    def _on_save_label_complete(self, future: Future, old_path: Path):
        try:
            new_path = future.result()
            self._set_ui_busy(False, status_message="Label saved successfully!")
            
            # Update ClipListView: remove old, add new
            self.clip_list_view.remove_selected_clip_from_list() # This should clear selection
            self.clip_list_view.add_clip_to_list(new_path)
            # self.clip_list_view.select_path(new_path) # Optional: auto-select the new item

            # Update ControlPanel to reflect the new path or clear if no auto-selection
            # self.control_panel.update_clip_details(new_path, status="Label saved", current_label=self.control_panel.get_current_label())
            # Instead of direct update, call handle_clip_selection to refresh everything consistently
            self.handle_clip_selection(new_path) # This will update details and button states
            # Ensure the status message from _set_ui_busy (called by _on_save_label_complete) is preserved
            # or set correctly by handle_clip_selection if it resets status.
            # For now, _set_ui_busy will be called after this, so its status message will take precedence.


        except Exception as e:
            self._set_ui_busy(False, status_message=f"Failed to save label: {e}")
            # If save fails, the selected path hasn't changed, refresh its state
            self.handle_clip_selection(old_path)


    def handle_save_label(self):
        selected_path = self.clip_list_view.get_selected_clip_path()
        if not selected_path or not self.clip_labeler_instance:
            print("No clip selected or labeler not initialized.")
            self.control_panel.update_clip_details(selected_path, status="Error: Generate label first.")
            return

        current_label_text = self.control_panel.get_current_label()
        if not current_label_text.strip():
            print("Label text is empty.")
            self.control_panel.update_clip_details(selected_path, status="Error: Label cannot be empty.", current_label="")
            return
        
        self._set_ui_busy(True, status_message="Saving label...")
        
        future = self.executor.submit(self._perform_save_label, current_label_text)
        self.after(100, lambda: self._check_future_status(future, lambda f: self._on_save_label_complete(f, selected_path)))

    def _check_future_status(self, future: Future, on_complete_callback: Callable[[Future], None]):
        """ Generic helper to check Future status and reschedule or call callback. """
        if future.done():
            on_complete_callback(future)
        else:
            self.after(100, lambda: self._check_future_status(future, on_complete_callback))

    def _perform_revert_rename(self, current_path: Path) -> tuple[Path, Path]:
        """
        Reverts a renamed file to its original path based on the log.
        This runs in the executor.
        Returns a tuple of (reverted_path (was new), original_path (now current)) if successful.
        Raises FileNotFoundError if log entry not found, or OSError on rename failure.
        """
        log_file_path = get_rename_log_path()
        if not log_file_path.exists():
            raise FileNotFoundError("Rename log file not found.")

        log_data: Dict[str, str] = {}
        try:
            with open(log_file_path, "r") as f:
                log_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise IOError(f"Error reading rename log: {e}") from e

        current_abs_path_str = str(current_path.resolve())
        if current_abs_path_str not in log_data:
            raise FileNotFoundError(f"'{current_path.name}' not found in rename log or path mismatch.")

        original_path_str = log_data[current_abs_path_str]
        original_path = Path(original_path_str)

        if original_path.exists():
            raise FileExistsError(f"Cannot revert: Original path '{original_path.name}' already exists.")

        try:
            current_path.rename(original_path)
            # If rename is successful, remove from log
            if not remove_from_rename_log(current_path): # current_path is the key in the log
                # Log a warning if removal failed, but proceed as rename was successful
                print(f"Warning: Rename successful, but failed to remove '{current_abs_path_str}' from log.")
            return current_path, original_path # (old_renamed_path, new_original_path)
        except OSError as e:
            raise OSError(f"Failed to revert rename for '{current_path.name}': {e}") from e


    def _on_revert_rename_complete(self, future: Future):
        try:
            reverted_path, original_path = future.result() # Unpack the paths
            
            self.clip_list_view.remove_selected_clip_from_list() # Remove the old (reverted) path
            self.clip_list_view.add_clip_to_list(original_path)   # Add the new (original) path
            
            # Update ControlPanel to reflect the new state
            # self.control_panel.update_clip_details(original_path, status="Reverted to original", current_label="")
            self.handle_clip_selection(original_path) # Refresh details and button states

            # Re-enable actions for the newly selected/reverted item
            self._set_ui_busy(False, status_message="Reverted successfully.")
            # handle_clip_selection should set the correct state for enable_actions and revert_button_state

        except FileNotFoundError as e: # Specific error from _perform_revert_rename
            self._set_ui_busy(False, status_message=str(e))
            self.handle_clip_selection(self.clip_list_view.get_selected_clip_path()) # Refresh current selection state
        except FileExistsError as e: # Specific error from _perform_revert_rename
            self._set_ui_busy(False, status_message=str(e))
            self.handle_clip_selection(self.clip_list_view.get_selected_clip_path())
        except OSError as e: # Specific error from _perform_revert_rename
            self._set_ui_busy(False, status_message=str(e))
            self.handle_clip_selection(self.clip_list_view.get_selected_clip_path())
        except Exception as e: # Catch-all for other future.result() issues or logic errors
            self._set_ui_busy(False, status_message=f"Revert rename failed: {e}")
            self.handle_clip_selection(self.clip_list_view.get_selected_clip_path())


    def handle_revert_rename(self):
        selected_path = self.clip_list_view.get_selected_clip_path()
        if not selected_path:
            self.control_panel.update_clip_details(None, status="Error: No clip selected to revert.")
            return

        self._set_ui_busy(True, status_message="Reverting rename...")
        
        future = self.executor.submit(self._perform_revert_rename, selected_path)
        self.after(100, lambda: self._check_future_status(future, self._on_revert_rename_complete))


def start_main_application():
    app = ClipTaleApp()
    app.mainloop()

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    # Start splash screen in a separate thread
    splash_thread = threading.Thread(target=show_splash_screen)
    splash_thread.start()

    # Start the main application
    start_main_application()
    
    # Splash screen manages its own lifecycle and closing via `after`.
    # Profiler will stop after main app loop finishes.
    profiler.disable()
    profiler.print_stats(sort="cumulative")
