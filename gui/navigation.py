import tkinter as tk
from tkinter import ttk

class NavigationPanel:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.checkbox_vars = {}
        self.context_update_callback = None
        self._create_widgets()
        
        
    def _create_widgets(self):
        # Canvas setup for scrollable area
        self.canvas = tk.Canvas(self.frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Inner frame for checkboxes
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # Event binding for scroll
        self.inner_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Layout
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.frame.grid(row=1, column=0, sticky="nswe")
        
        # Style configuration
        style = ttk.Style()
        style.configure("Nav.TCheckbutton", padding=5)
        style.configure("Nav.TLabel", padding=5)

    def add_message(self, idx, entry_idx, message, checked=True):
        frame = ttk.Frame(self.inner_frame)
        frame.pack(fill=tk.X, pady=2)
        
        # Checkbox
        var = tk.BooleanVar(value=checked)
        self.checkbox_vars[entry_idx] = var
        chk = ttk.Checkbutton(
            frame,
            variable=var,
            style="Nav.TCheckbutton",
            command=lambda: self._update_context_state(entry_idx, var)  # Simplified
        )
        chk.pack(side=tk.LEFT)
        
        # Label with message preview
        lbl = ttk.Label(
            frame,
            text=f"{idx}. {self._truncate_message(message)}",
            style="Nav.TLabel",
            cursor="hand2",
            wraplength=120
        )
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl.bind("<Button-1>", lambda e: self.selection_callback(entry_idx))

    def _truncate_message(self, message):
        return (message[:35] + '...') if len(message) > 35 else message

    def on_context_update(self, callback):
        self.context_update_callback = callback
    
    def _update_context_state(self, entry_idx, var):
        # Update current message and corresponding response
        """Handle checkbox state changes through callback"""
        if self.context_update_callback:
            # Only pass the state change to the main controller
            self.context_update_callback(entry_idx, var.get())

    def on_select(self, callback):
        self.selection_callback = callback

    def clear(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()
