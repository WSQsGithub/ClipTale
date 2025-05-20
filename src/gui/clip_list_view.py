import customtkinter as ctk
from pathlib import Path
from typing import Dict, Optional, Callable # Added Callable

class ClipListView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Video Clips")
        self.scrollable_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.clips_data: Dict[ctk.CTkLabel, Path] = {} # Map label widget to Path
        self.selected_clip_widget: Optional[ctk.CTkLabel] = None
        self.selection_changed_callback: Optional[Callable[[Optional[Path]], None]] = None # Callback

        # Store default colors for selection feedback
        self._default_bg_color = self.cget("fg_color") # Get default frame background
        # For labels, need to get their default bg color or use transparent and rely on frame's bg for deselected state.
        # Let's assume labels will have their own background color, which might be different from the frame.
        # A common approach is to set a specific selection color.
        self._selected_color = "gray30" # Example selection color

    def _handle_clip_selection_event(self, event):
        clicked_widget = event.widget
        
        # Deselect previously selected widget
        if self.selected_clip_widget:
            # Attempt to restore original color; this depends on how labels are configured.
            # If labels are transparent, their effective bg is the frame's bg.
            # For simplicity, let's assume we set a specific background on selection and remove it (or set to default) on deselection.
            # This requires knowing the original color of the label.
            # A more robust way is to use widget.cget("fg_color") before changing it, but that's complex if colors vary.
            # Let's assume all labels have the same default background color (e.g., transparent or a common theme color)
            # For CTkLabel, the default fg_color is ('#F9F9FA', '#343638'), text_color is default.
            # We are changing the whole widget's background (fg_color for CTk widgets).
            self.selected_clip_widget.configure(fg_color=self.selected_clip_widget.cget("fg_color")) # Get its original color
            # Or, more simply, if all labels have a known default:
            # self.selected_clip_widget.configure(fg_color=self._default_label_bg_color) # Need to define this

        # Select new widget
        if clicked_widget in self.clips_data: # Check if it's a clip label
            self.selected_clip_widget = clicked_widget
            self.selected_clip_widget.configure(fg_color=self._selected_color) # Highlight selected

        # Notify main app about selection change
        if self.selection_changed_callback:
            selected_path = self.get_selected_clip_path()
            self.selection_changed_callback(selected_path)

    def add_clip_to_list(self, video_path: Path):
        clip_name = video_path.name
        # Create a new label for the clip.
        # Make it expand horizontally.
        # TODO: Decide on label background color for deselected state.
        # For now, use default label fg_color.
        label = ctk.CTkLabel(self.scrollable_frame, text=clip_name, anchor="w")
        label.pack(fill="x", padx=5, pady=2) # Pack labels tightly, expand horizontally
        
        label.bind("<Button-1>", self._handle_clip_selection_event)
        self.clips_data[label] = video_path

    def get_selected_clip_path(self) -> Optional[Path]:
        if self.selected_clip_widget and self.selected_clip_widget in self.clips_data:
            return self.clips_data[self.selected_clip_widget]
        return None

    def remove_selected_clip_from_list(self) -> Optional[Path]:
        removed_path: Optional[Path] = None
        if self.selected_clip_widget and self.selected_clip_widget in self.clips_data:
            removed_path = self.clips_data.pop(self.selected_clip_widget)
            self.selected_clip_widget.destroy()
            self.selected_clip_widget = None
            
            # Also notify that selection has changed (to None)
            if self.selection_changed_callback:
                self.selection_changed_callback(None)
        return removed_path


if __name__ == '__main__':
    root = ctk.CTk()
    root.title("ClipListView Test")
    root.geometry("300x500") # Increased height for scrollable content

    clip_list_view = ClipListView(master=root)
    clip_list_view.pack(fill="both", expand=True, padx=10, pady=10)

    # Example of how selection_changed_callback would be used by an external component
    def on_selection_changed(selected_path: Optional[Path]):
        if selected_path:
            print(f"Selection changed: {selected_path.name}")
        else:
            print("Selection cleared.")
    
    clip_list_view.selection_changed_callback = on_selection_changed

    # Add some dummy clips for testing
    dummy_paths = [
        Path("/path/to/video1.mp4"),
        Path("/another/path/clip_alpha.mkv"),
        Path("/videos/test_beta.avi"),
        Path("/movies/final_cut_pro.mov"),
        Path("/tmp/short_sample.mp4"),
    ]
    for p in dummy_paths:
        clip_list_view.add_clip_to_list(p)
    
    # Button to test removal
    def remove_action():
        removed = clip_list_view.remove_selected_clip_from_list()
        if removed:
            print(f"Removed: {removed.name}")
        else:
            print("Nothing selected to remove.")

    remove_button = ctk.CTkButton(root, text="Remove Selected", command=remove_action)
    remove_button.pack(pady=5)

    root.mainloop()
