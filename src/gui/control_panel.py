import customtkinter as ctk
from pathlib import Path
from typing import Optional

class ControlPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1) # Allow content to expand horizontally

        # --- File Operations Section ---
        self.file_ops_frame = ctk.CTkFrame(self)
        self.file_ops_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.file_ops_frame.grid_columnconfigure(0, weight=1) # Button 1
        self.file_ops_frame.grid_columnconfigure(1, weight=1) # Button 2

        self.add_videos_button = ctk.CTkButton(self.file_ops_frame, text="Add Video(s)")
        self.add_videos_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.remove_selected_button = ctk.CTkButton(self.file_ops_frame, text="Remove Selected")
        self.remove_selected_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # --- Actions Section (for selected clip) ---
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=1, column=0, padx=10, pady=(5,5), sticky="ew")
        self.actions_frame.grid_columnconfigure(0, weight=1) # Button 1
        self.actions_frame.grid_columnconfigure(1, weight=1) # Button 2

        self.generate_label_button = ctk.CTkButton(self.actions_frame, text="Generate Label")
        self.generate_label_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.save_label_button = ctk.CTkButton(self.actions_frame, text="Save Label (Rename File)")
        self.save_label_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Add Revert Rename button in a new row within actions_frame
        # Configure another column for the new button, or let it span if only one button in the new row.
        # For simplicity, let it span if it's the only one in its row.
        # Or, add it to a new frame to control its width better.
        # Let's add a new row in the same actions_frame, spanning both columns for now.
        self.revert_rename_button = ctk.CTkButton(self.actions_frame, text="Revert Rename")
        self.revert_rename_button.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")
        
        # --- Selected Clip Details Section ---
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew") # Changed row to 2
        self.grid_rowconfigure(2, weight=1) # Allow details_frame to expand vertically (Changed row to 2)
        
        self.details_frame.grid_columnconfigure(1, weight=1) # Configure column 1 (values) to expand

        row_idx = 0
        # Filename
        self.filename_label_static = ctk.CTkLabel(self.details_frame, text="Filename:", anchor="w")
        self.filename_label_static.grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        self.filename_value = ctk.CTkLabel(self.details_frame, text="N/A", anchor="w")
        self.filename_value.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Filepath
        self.filepath_label_static = ctk.CTkLabel(self.details_frame, text="Filepath:", anchor="w")
        self.filepath_label_static.grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        self.filepath_value = ctk.CTkLabel(self.details_frame, text="N/A", anchor="w")
        self.filepath_value.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Status
        self.status_label_static = ctk.CTkLabel(self.details_frame, text="Status:", anchor="w")
        self.status_label_static.grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        self.status_value = ctk.CTkLabel(self.details_frame, text="N/A", anchor="w")
        self.status_value.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1
        
        # Current Label
        self.current_label_static = ctk.CTkLabel(self.details_frame, text="Current Label:", anchor="w")
        self.current_label_static.grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        self.current_label_entry = ctk.CTkEntry(self.details_frame, placeholder_text="Generated label will appear here") # Changed to CTkEntry
        self.current_label_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Add a spacer row to push details to the top if frame expands
        self.details_frame.grid_rowconfigure(row_idx, weight=1)

        # Initialize button states
        self.enable_actions(False) # Initially disabled as no clip is selected


    def update_clip_details(self, video_path: Optional[Path], status: str = "New", current_label: str = ""):
        if video_path:
            self.filename_value.configure(text=video_path.name)
            self.filepath_value.configure(text=str(video_path))
            self.status_value.configure(text=status)
            self.set_current_label(current_label if current_label else "") # Use new method
            self.enable_actions(True) # Enable actions when a clip is selected
        else:
            self.filename_value.configure(text="N/A")
            self.filepath_value.configure(text="N/A")
            self.status_value.configure(text="N/A")
            self.set_current_label("") # Clear label entry
            self.enable_actions(False) # Disable actions if no clip

    def get_current_label(self) -> str:
        return self.current_label_entry.get()

    def set_current_label(self, label: str):
        # Clear existing text first
        self.current_label_entry.delete(0, ctk.END)
        if label: # Only insert if label is not empty, otherwise it's already cleared
            self.current_label_entry.insert(0, label)

    def enable_actions(self, enable: bool):
        state = ctk.NORMAL if enable else ctk.DISABLED
        self.generate_label_button.configure(state=state)
        self.save_label_button.configure(state=state)
        # self.revert_rename_button.configure(state=state) # Revert button is now handled separately
        # The label entry should generally be editable if a clip is selected,
        # but might be read-only during generation. For now, keep it always editable.
        # self.current_label_entry.configure(state=state) # This would make it read-only too

    def set_revert_button_state(self, enable: bool):
        """Specifically sets the state of the Revert Rename button."""
        state = ctk.NORMAL if enable else ctk.DISABLED
        self.revert_rename_button.configure(state=state)

    def enable_file_operations(self, enable: bool):
        state = ctk.NORMAL if enable else ctk.DISABLED
        self.add_videos_button.configure(state=state)
        self.remove_selected_button.configure(state=state)


if __name__ == '__main__':
    root = ctk.CTk()
    root.title("ControlPanel Test")
    root.geometry("400x500") # Adjusted size for new buttons
    
    control_panel = ControlPanel(master=root)
    control_panel.pack(fill="both", expand=True, padx=10, pady=10)

    # Example: Test update_clip_details & button states
    def test_select_clip():
        dummy_path = Path("/path/to/dummy_video.mp4")
        control_panel.update_clip_details(dummy_path, status="Selected", current_label="initial_test_label")
        print(f"Label from entry: {control_panel.get_current_label()}")
    
    def test_deselect_clip():
        control_panel.update_clip_details(None)

    def test_disable_all():
        control_panel.enable_actions(False)
        control_panel.enable_file_operations(False)

    def test_enable_all():
        # Note: enable_actions(True) is called by update_clip_details when a clip is selected.
        # This direct call is just for testing the method itself.
        control_panel.enable_actions(True) 
        control_panel.enable_file_operations(True)


    test_button_select = ctk.CTkButton(root, text="Test Select Clip", command=test_select_clip)
    test_button_select.pack(pady=5)
    
    test_button_deselect = ctk.CTkButton(root, text="Test Deselect Clip", command=test_deselect_clip)
    test_button_deselect.pack(pady=5)

    test_button_disable = ctk.CTkButton(root, text="Test Disable All Buttons", command=test_disable_all)
    test_button_disable.pack(pady=5)

    test_button_enable = ctk.CTkButton(root, text="Test Enable All Buttons", command=test_enable_all)
    test_button_enable.pack(pady=5)
    
    # Initial state for testing
    control_panel.update_clip_details(None) 
    control_panel.set_current_label("Test Initial Text")


    root.mainloop()
