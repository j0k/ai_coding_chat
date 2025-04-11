import tkinter as tk
from tkinter import ttk, scrolledtext

class ChatPanel:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        # Chat history
        self.history = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, state='normal',
            font=('Arial', 10), spacing3=5
        )
        self.history.tag_config('user', foreground='#006400')
        self.history.tag_config('assistant', foreground='#00008B')
        self.history.tag_config('system', foreground='#8B0000')
        
        # Input area
        self.input = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, height=3,
            font=('Arial', 10), undo=True
        )
        self.send_btn = ttk.Button(self.frame, text="Send")
        
        # Layout
        self.history.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.input.grid(row=1, column=0, sticky="ew")
        self.send_btn.grid(row=1, column=1, padx=5)
        self.frame.grid(row=1, column=1, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

    def on_send(self, callback):
        self.send_callback = callback
        self.send_btn.config(command=self._send_message)
        self.input.bind("<Return>", self._handle_enter)

    def update_font(self, font_name):
        self.history.config(font=(font_name, 10))
        self.input.config(font=(font_name, 10))

    def _send_message(self):
        message = self.input.get("1.0", tk.END).strip()
        if message:
            self.send_callback(message)
            self.input.delete("1.0", tk.END)

    def _handle_enter(self, event):
        if event.state == 0:
            self._send_message()
            return "break"
        return None
