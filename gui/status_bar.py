from tkinter import ttk
import tkinter as tk

class StatusBar:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        self.progress_bar = ttk.Progressbar(
            self.frame, mode='determinate', length=100
        )
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.status_label.pack(side=tk.RIGHT, padx=5)
        self.frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

    def set_status(self, message):
        self.status_var.set(message)

    def start_progress(self):
        self.progress_bar.start()

    def stop_progress(self):
        self.progress_bar.stop()
