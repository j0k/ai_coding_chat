import tkinter as tk
from tkinter import ttk
from .command_tab import CommandTab
from .ai_flow_tab import AIFlowTab

class MemoPanel:
    def __init__(self, parent, chat_panel, root):
        self.parent = parent
        self.chat_panel = chat_panel
        self.root = root
        self.is_visible = False
        self.is_expanded = False
        self.min_width = 50
        self.max_width = 500

        self.frame = ttk.Frame(parent, width=50)
        self.frame.pack_propagate(False)
        self._create_widgets()
        #self._setup_bindings()


        # Start in collapsed state
        self.collapse()
        #self.frame.grid(row=1, column=1, sticky="nswe")
        #self.frame.grid_propagate(False)
        #self.toggle_visibility()

    def _create_widgets(self):
        # Header
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill=tk.X)

        self.toggle_btn = ttk.Button(
            self.header_frame,
            text="◀",
            width=3,
            command=self.toggle_visibility
        )
        self.toggle_btn.pack(side=tk.RIGHT)

        # Main content area (initially hidden)
        self.content = ttk.Frame(self.frame)

        # Add your actual memo panel widgets here
        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Add tabs (example)
        self.command_tab = CommandTab(self.notebook, self.root, self.chat_panel)
        self.ai_flow_tab = AIFlowTab(self.notebook, self.root, self.chat_panel)

        self.notebook.add(self.command_tab.frame, text="Commands")
        self.notebook.add(self.ai_flow_tab.frame, text="AI Flows")

        # # Notebook container
        # self.notebook_container = ttk.Frame(self.frame)
        # self.notebook = ttk.Notebook(self.notebook_container)
        #
        # # Create tabs
        # self.command_tab = CommandTab(self.notebook, self.root, self.chat_panel)
        # self.flow_tab = AIFlowTab(self.notebook, self.root, self.chat_panel)
        #
        # self.notebook.add(self.command_tab.frame, text="Commands")
        # self.notebook.add(self.flow_tab.frame, text="AI Flows")
        # self.notebook.pack(fill=tk.BOTH, expand=True)
        # self.notebook_container.pack(fill=tk.BOTH, expand=True)

    def toggle_visibility(self):
        if self.is_expanded:
            self.collapse()
            #self.frame.config(width=50)
            #self.notebook_container.pack_forget()
            #self.toggle_btn.config(text="▶")
            #self.is_visible = False
            #self.frame.config(width=50)
        else:
            self.expand()
            # self.frame.config(width=300)
            # self.notebook_container.pack(fill=tk.BOTH, expand=True)
            # self.toggle_btn.config(text="◀")
            # self.is_visible = True

    def collapse(self):
        """Minimize the panel"""
        self.frame.config(width=self.min_width)
        self.content.pack_forget()  # Hide content
        self.toggle_btn.config(text="»")  # Right arrow
        self.is_expanded = False

    def expand(self):
        """Expand the panel"""
        self.frame.config(width=self.max_width)
        self.content.pack(fill=tk.BOTH, expand=True)  # Show content
        self.toggle_btn.config(text="«")  # Left arrow
        self.is_expanded = True
