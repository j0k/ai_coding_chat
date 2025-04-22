import tkinter as tk
from tkinter import ttk

class NavigationPanel:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.checkbox_vars = {}  # Stores checkbox states by entry_id
        self.badges = {}        # Stores badge variables by entry_id
        self.message_frames = {} # Stores frame references by entry_id
        self.context_update_callback = None
        self.selection_callback = None
        self._create_widgets()

    def _create_widgets(self):
        # Configure styles
        style = ttk.Style()
        style.configure("Nav.TCheckbutton", padding=5)
        style.configure("Nav.TLabel", padding=5)
        style.configure('Badge.TLabel',
            background='#e1e1e1',
            foreground='#555555',
            relief='ridge',
            font=('Arial', 9, 'italic'),  # Italic for N/A
            anchor='center',
            borderwidth=1,
            padding=(3,1)
        )

        # Canvas setup for scrollable area
        self.canvas = tk.Canvas(self.frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Inner frame for messages
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Event binding for scroll
        self.inner_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Layout
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.frame.grid(row=1, column=0, sticky="nswe")

    def add_message(self, idx, entry_id, message, checked=True, execution_time=None):
        """Add a new message to the navigation panel"""
        frame = ttk.Frame(self.inner_frame)
        frame.pack(fill=tk.X, pady=2)
        self.message_frames[entry_id] = frame

        # Checkbox
        var = tk.BooleanVar(value=checked)
        self.checkbox_vars[entry_id] = var
        chk = ttk.Checkbutton(
            frame,
            variable=var,
            style="Nav.TCheckbutton",
            command=lambda: self._update_context_state(entry_id, var)
        )
        chk.pack(side=tk.LEFT)

        # Message label
        lbl = ttk.Label(
            frame,
            text=f"{idx}. {self._truncate_message(message)}",
            style="Nav.TLabel",
            cursor="hand2",
            wraplength=120
        )
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl.bind("<Button-1>", lambda e: self.selection_callback(entry_id))

        # Execution time badge
        badge_var = tk.StringVar()
        initial_text = f"{execution_time:.1f}s" if execution_time is not None else "N/A"
        ttk.Label(
            frame,
            textvariable=badge_var,
            style='Badge.TLabel',
            width=8
        ).pack(side=tk.RIGHT)
        self.badges[entry_id] = badge_var
        badge_var.set(initial_text)

        # Scroll to show new message
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.inner_frame.update_idletasks()

    def update_badge(self, entry_id, text):  # Changed parameter name
        badge_text = text if text else "N/A"
        if entry_id in self.badges:
            self.badges[entry_id].set(badge_text)  # Use entry_id as key

    def _truncate_message(self, message):
        """Create shortened message preview"""
        return (message[:35] + '...') if len(message) > 35 else message

    def _update_context_state(self, entry_id, var):
        """Handle checkbox state changes"""
        if self.context_update_callback:
            self.context_update_callback(entry_id, var.get())

    def on_context_update(self, callback):
        """Register context update callback"""
        self.context_update_callback = callback

    def on_select(self, callback):
        """Register message selection callback"""
        self.selection_callback = callback

    def clear(self):
        """Clear all messages from the navigation panel"""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()
        self.badges.clear()
        self.message_frames.clear()

    def highlight_message(self, entry_id, duration=2000):
        """Temporarily highlight a message"""
        if entry_id in self.message_frames:
            frame = self.message_frames[entry_id]
            frame.configure(style='Highlight.TFrame')
            self.parent.after(duration, lambda: frame.configure(style='TFrame'))
