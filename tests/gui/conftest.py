import pytest
from unittest.mock import MagicMock, patch
import asyncio # Keep for spec if any asyncio parts are directly used by app
from concurrent.futures import ThreadPoolExecutor # For spec

# Assuming these are the actual paths for the classes used by ClipTaleApp
from src.gui.ui import ClipTaleApp
from src.gui.clip_list_view import ClipListView
from src.gui.control_panel import ControlPanel

@pytest.fixture
def app(mocker):
    # Mock all CustomTkinter UI elements to avoid actual window creation
    mocker.patch('customtkinter.CTk')
    mocker.patch('customtkinter.CTkFrame')
    mocker.patch('customtkinter.CTkLabel')
    mocker.patch('customtkinter.CTkButton')
    mocker.patch('customtkinter.CTkEntry')
    mocker.patch('customtkinter.CTkScrollableFrame')
    
    # Mock other parts that ClipTaleApp might initialize or call globally
    mocker.patch('src.gui.ui.show_splash_screen') # Called in ui.py's main block, not by App instance
    mocker.patch('customtkinter.filedialog.askopenfilenames')

    # Mock threading and asyncio event loop if app manages its own (ClipTaleApp doesn't directly)
    # mocker.patch('asyncio.new_event_loop') # Not directly used by ClipTaleApp init
    # mocker.patch('threading.Thread') # Splash screen thread is outside app instance

    # Create the app instance
    # We need to ensure that the __init__ of ClipTaleApp can run.
    # It instantiates ClipListView and ControlPanel, and sets up an executor.
    # These will be replaced by mocks after instantiation.
    
    # Temporarily allow original instantiation of internal components
    # then replace them with mocks for testing specific interactions.
    
    # Patch the ThreadPoolExecutor before app instantiation if app creates it in __init__
    mock_executor_instance = MagicMock(spec=ThreadPoolExecutor)
    mocker.patch('concurrent.futures.ThreadPoolExecutor', return_value=mock_executor_instance)

    _app = ClipTaleApp()
    
    # Now, replace the internally created collaborators with mocks for fine-grained control
    # This is important if their actual methods would be called during tests and we want to control them.
    _app.clip_list_view = MagicMock(spec=ClipListView)
    _app.control_panel = MagicMock(spec=ControlPanel)
    
    # The executor is already mocked by the class-level patch above,
    # so _app.executor is already a MagicMock.
    # We can assign it again if we want a fresh mock not tied to the class patch, but it's usually not needed.
    # _app.executor = mock_executor_instance # This is already done by the patch

    # Mock the 'after' method which is part of CTk/Tkinter, used for scheduling
    # This is crucial for testing methods that use self.after to check futures
    _app.after = MagicMock()

    return _app
