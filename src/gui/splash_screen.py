import threading
import time

import customtkinter as ctk


class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Loading...")
        self.geometry("300x200")
        self.label = ctk.CTkLabel(self, text="Loading, please wait...")
        self.label.pack(pady=20)
        self.progress = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.progress.pack(pady=20, padx=20)
        self.progress.start()

    def close(self):
        self.progress.stop()
        self.destroy()


def show_splash_screen():
    splash = SplashScreen()
    splash.after(3000, splash.close)  # Close after 3 seconds
    splash.mainloop()


def start_app():
    # Simulate some startup tasks
    time.sleep(2)  # Simulate delay
    app = ctk.CTk()
    app.title("ClipTale App")
    app.geometry("400x300")

    def button_callback():
        result = "Functional code executed!"
        label.configure(text=f"Result: {result}")

    button = ctk.CTkButton(app, text="Run Functional Code", command=button_callback)
    button.pack(pady=20)

    label = ctk.CTkLabel(app, text="Click the button to start")
    label.pack(pady=10)

    app.mainloop()
