import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess

class MemoPanel:
    def __init__(self, parent, chat_panel, root):
        self.parent = parent
        self.chat_panel = chat_panel
        self.root = root
        self.is_visible = True
        self._create_widgets()
        self.frame.grid(row=1, column=2, sticky="nswe")
        self.frame.grid_propagate(False)
        self.toggle_visibility()

    def _create_widgets(self):
        # Main frame setup
        self.frame = ttk.Frame(self.parent, width=300)
        self.frame.grid_propagate(False)

        # Header with toggle button
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill=tk.X, pady=5)

        self.toggle_btn = ttk.Button(
            self.header_frame,
            text="◀",
            width=3,
            command=self.toggle_visibility
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        self.title = ttk.Label(
            self.header_frame,
            text="Memo & Prompt Editor",
            font=('Arial', 10, 'bold')
        )
        self.title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Command panel
        self.command_frame = ttk.Frame(self.frame)
        self.command_frame.pack(fill=tk.X, pady=5)

        # Command selector
        self.cmd_var = tk.StringVar()
        self.cmd_combo = ttk.Combobox(
            self.command_frame,
            textvariable=self.cmd_var,
            values=[
                "tree -L 2",
                "python3 tools/listfiles.py -int ,py,md,txt"
            ],
            state="readonly",
            width=25
        )
        self.cmd_combo.pack(side=tk.LEFT, padx=5)
        self.cmd_combo.bind("<<ComboboxSelected>>", self._insert_command)

        # Execute button
        self.execute_btn = ttk.Button(
            self.command_frame,
            text="Run Command",
            command=self.execute_command
        )
        self.execute_btn.pack(side=tk.RIGHT, padx=5)

        # Text area
        self.text_area = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            font=('Monaco', 10),
            undo=True,
            height=20,
            padx=5,
            pady=5
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Button panel
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, pady=5)

        # Action buttons
        self.clear_btn = ttk.Button(
            self.button_frame,
            text="Clear",
            command=self.clear_text
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = ttk.Button(
            self.button_frame,
            text="Copy to Chat",
            command=self.copy_to_chat
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=5)

    def toggle_visibility(self):
        if self.is_visible:
            # Collapse panel - hide everything except header
            self.command_frame.pack_forget()
            self.text_area.pack_forget()
            self.button_frame.pack_forget()
            self.frame.config(width=30)
            self.title.config(text="")
            self.toggle_btn.config(text="▶")
            self.parent.grid_columnconfigure(2, minsize=30)
        else:
            # Expand panel - show all elements
            self.command_frame.pack(fill=tk.X, pady=5)
            self.text_area.pack(fill=tk.BOTH, expand=True)
            self.button_frame.pack(fill=tk.X, pady=5)
            self.frame.config(width=300)
            self.title.config(text="Memo & Prompt Editor")
            self.toggle_btn.config(text="◀")
            self.parent.grid_columnconfigure(2, minsize=300)

        self.is_visible = not self.is_visible
        self.parent.update_idletasks()

    def clear_text(self):
        self.text_area.delete('1.0', tk.END)

    def copy_to_chat(self):
        text = self.text_area.get('1.0', tk.END).strip()
        if text and self.chat_panel:  # Use stored reference
            self.chat_panel.input.delete('1.0', tk.END)
            self.chat_panel.input.insert('1.0', text)
            self.chat_panel.input.focus()

    def get_text(self):
        return self.text_area.get('1.0', tk.END).strip()

    def set_text(self, text):
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', text)


    def _insert_command(self, event):
        selected = self.cmd_var.get()
        if selected:
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', selected)

    def execute_command(self):
        command = self.text_area.get('1.0', tk.END).strip()
        if not command:
            return

        def run_command():
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd="."  # Run from project root
                )
                output = result.stdout
            except subprocess.CalledProcessError as e:
                output = f"Error {e.returncode}:\n{e.stderr}\n{e.stdout}"
            except Exception as e:
                output = f"Execution failed: {str(e)}"

            self.root.after(0, lambda: self._show_command_output(output))

        threading.Thread(target=run_command, daemon=True).start()
        self.text_area.insert(tk.END, "\n\nRunning command...")

    def _show_command_output(self, output):
        self.text_area.insert(tk.END, f"{output}")
        self.text_area.see(tk.END)
