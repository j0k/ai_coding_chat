import tkinter as tk
from tkinter import ttk

class Toolbar:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        # Export/Load buttons
        self.export_btn = ttk.Button(self.frame, text="Export Session")
        self.load_btn = ttk.Button(self.frame, text="Load Session")
        
        # Font selection
        self.font_var = tk.StringVar(value="Arial")
        self.font_combo = ttk.Combobox(
            self.frame,
            textvariable=self.font_var,
            values=["Arial", "Courier New", "Times New Roman"],
            state="readonly",
            width=15
        )
        
        # Context checkbox
        self.use_context_var = tk.BooleanVar(value=True)
        self.context_check = ttk.Checkbutton(
            self.frame,
            text="Use Context",
            variable=self.use_context_var
        )
        
        # Model selection
        self.available_models = [
            'deepseek-chat',
            'deepseek-coder-33b-instruct',
            'deepseek-math-7b-instruct',
            'deepseek-reasoner'
        ]
        self.model_var = tk.StringVar(value=self.available_models[0])
        self.model_select = ttk.Combobox(
            self.frame,
            textvariable=self.model_var,
            values=self.available_models,
            state="readonly",
            width=25
        )
        
        # Temperature controls
        self.temperature = tk.DoubleVar(value=0.7)
        self.temp_slider = ttk.Scale(
            self.frame,
            from_=0,
            to=1,
            variable=self.temperature,
            orient="horizontal"
        )
        self.temp_label = ttk.Label(self.frame, text="0.7", width=4)
        
        # Layout
        self.export_btn.pack(side=tk.LEFT, padx=2)
        self.load_btn.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.frame, text="Font:").pack(side=tk.LEFT, padx=(10, 2))
        self.font_combo.pack(side=tk.LEFT)
        self.context_check.pack(side=tk.LEFT, padx=10)

        self.timeout_var = tk.BooleanVar(value=False)  # Default unchecked
        
        # Add timeout checkbox
        self.timeout_check = ttk.Checkbutton(
            self.frame,
            text="Enable Timeout (15s)",
            variable=self.timeout_var,
            command=self._update_timeout_state
        )
        self.timeout_check.pack(side=tk.LEFT, padx=10)

        ttk.Label(self.frame, text="Model:").pack(side=tk.LEFT, padx=5)
        self.model_select.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.frame, text="Temp:").pack(side=tk.LEFT, padx=5)
        self.temp_slider.pack(side=tk.LEFT, padx=5)
        self.temp_label.pack(side=tk.LEFT, padx=5)
        
        self.frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

    def _update_timeout_state(self):
        """Handle timeout checkbox changes"""
        if self.timeout_update_callback:
            self.timeout_update_callback(self.timeout_var.get())

    def on_timeout_change(self, callback):
        """Register timeout change callback"""
        self.timeout_update_callback = callback

    def on_export(self, callback):
        self.export_btn.config(command=callback)

    def on_load(self, callback):
        self.load_btn.config(command=callback)

    def on_font_change(self, callback):
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: callback(self.font_var.get()))

    def on_temp_change(self, callback):
        self.temp_slider.config(command=lambda v: self._update_temp(v, callback))

    def _update_temp(self, value, callback):
        self.temp_label.config(text=f"{float(value):.1f}")
        callback(float(value))
