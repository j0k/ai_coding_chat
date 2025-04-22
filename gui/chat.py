import tkinter as tk
from tkinter import ttk, scrolledtext

class ChatPanel:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._bind_events()
        self.resize_start_y = None
        self.initial_height = 3  # Default height in lines

    def _create_widgets(self):
        # Chat history
        self.history = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, state='normal',
            font=('Monaco', 10), spacing3=5
        )
        self.history.tag_config('user', foreground='#006400')
        self.history.tag_config('assistant', foreground='#00008B')
        self.history.tag_config('system', foreground='#8B0000')
        self.history.tag_config('highlight',
            background='#f0f0f0',
            relief='ridge',
            borderwidth=1
        )

        # Resize handle
        self.handle = ttk.Frame(self.frame, height=5, cursor='sb_v_double_arrow')
        self.handle.bind("<ButtonPress-1>", self._start_resize)
        self.handle.bind("<B1-Motion>", self._do_resize)
        self.handle.bind("<ButtonRelease-1>", self._stop_resize)

        # Input area
        self.input = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, height=5,
            font=('Arial', 10), undo=True
        )
        self.send_btn = ttk.Button(self.frame, text="Send")
        style = ttk.Style()
        style.configure('Disabled.TButton',
            foreground='gray',
            background='#f0f0f0',
            relief='flat'
        )

        # Layout
        self.history.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.input.grid(row=1, column=0, sticky="ew")
        self.send_btn.grid(row=1, column=1, padx=5)
        self.frame.grid(row=1, column=1, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

    def _bind_events(self):
        self.send_btn.config(command=self._send_message)
        self.input.bind("<Return>", self._handle_enter)

    def _start_resize(self, event):
        self.resize_start_y = event.y_root
        self.initial_height = self.input.cget("height")

    def _do_resize(self, event):
        if self.resize_start_y is None:
            return

        delta = event.y_root - self.resize_start_y
        line_height = self.input.winfo_height() / self.initial_height
        new_height = max(1, min(int(self.initial_height + delta/line_height), 10))

        self.input.config(height=new_height)
        self.input_frame.update_idletasks()

    def _stop_resize(self, event):
        self.resize_start_y = None

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

    def enable_send_button(self):
        """Enable the send button with visual feedback"""
        self.send_btn.config(
            state=tk.NORMAL,
            text="Send",
            style='TButton'  # Reset to default style
        )
        self.send_btn.update_idletasks()

    def disable_send_button(self):
        """Disable the send button with visual feedback"""
        self.send_btn.config(
            state=tk.DISABLED,
            text="Sending...",
            style='Disabled.TButton'
        )
        self.send_btn.update_idletasks()

    def _handle_enter(self, event):
        if event.state == 0:
            self._send_message()
            return "break"
        return None
