import tkinter as tk
from tkinter import ttk, scrolledtext
from IPython.terminal.embed import InteractiveShellEmbed
import io
import sys
import threading
from pyte import Screen, Stream

class ChatPanel:
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.root = parent.winfo_toplevel()
        self.terminal_visible = True

        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._bind_events()
        self.resize_start_y = None
        self.initial_height = 3  # Default height in lines
        self._create_terminal()
        self._bind_terminal_events()

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

    def toggle_terminal(self):
        """Toggle terminal visibility"""
        if not hasattr(self, 'terminal_frame'):
            self._create_terminal()

        if self.terminal_visible:
            self.terminal_frame.grid_remove()
        else:
            self.terminal_frame.grid()
            self.term_input.focus()

        self.terminal_visible = not self.terminal_visible
        self._adjust_chat_layout()

    def _adjust_chat_layout(self):
        """Adjust chat layout based on terminal visibility"""
        if self.terminal_visible:
            self.history.grid(row=0, column=0, columnspan=2, sticky="nsew")
            self.terminal_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
            self.input.grid(row=2, column=0, sticky="ew")
            self.send_btn.grid(row=2, column=1, padx=5)
        else:
            self.history.grid(row=0, column=0, columnspan=2, sticky="nsew")
            self.input.grid(row=1, column=0, sticky="ew")
            self.send_btn.grid(row=1, column=1, padx=5)

    def _create_terminal(self):
        # Terminal container
        self.terminal_frame = ttk.Frame(self.frame)
        self.terminal_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Terminal display
        self.term_display = scrolledtext.ScrolledText(
            self.terminal_frame,
            wrap=tk.WORD,
            height=8,
            font=('Monaco', 9),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        self.term_display.pack(fill=tk.BOTH, expand=True)

        # Input line
        self.term_input = ttk.Entry(self.terminal_frame)
        self.term_input.pack(fill=tk.X, padx=5, pady=5)

        # Initialize IPython shell
        self._init_ipython()

        # Collapse by default
        #self.terminal_visible = False
        #self.toggle_terminal()

    def _init_ipython(self):
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        TerminalInteractiveShell.instance().loop_runner = "sync"

        self.shell = InteractiveShellEmbed(
            banner1="",
            exit_msg="",
            user_ns={
                'send': self._send_from_terminal,
                'app': self.app
            },
            display_banner=False,
            colors='neutral'
        )
        self.shell.displayhook = self._handle_display
        self.captured_io = io.StringIO()

        # Redirect stdio
        sys.stdout = self
        sys.stderr = self

        # Create pyte screen
        self.term_width = 80
        self.term_height = 24
        self.screen = Screen(self.term_width, self.term_height)
        self.stream = Stream(self.screen)

    def _bind_terminal_events(self):
        self.term_input.bind("<Return>", self._execute_terminal_command)
        self.term_display.bind("<Configure>", self._update_term_size)
        self.root.bind("<Control-t>", lambda e: self.toggle_terminal())

    def toggle_terminal(self):
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self.terminal_frame.grid()
            self.term_input.focus()
        else:
            self.terminal_frame.grid_remove()

    def _update_term_size(self, event):
        cols = event.width // 8  # Approximate character width
        rows = event.height // 16  # Approximate row height
        self.screen.resize(rows, cols)

    def _execute_terminal_command(self, event):
        command = self.term_input.get()
        if not command.strip():
            return

        self.term_input.delete(0, tk.END)
        self._update_term_display(f"\n>>> {command}\n")

        # Run in thread
        threading.Thread(
            target=self._run_ipython_command,
            args=(command,),
            daemon=True
        ).start()

    def _run_ipython_command(self, command):
        try:
            # Create fresh StringIO for capturing output
            captured_output = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured_output

            # Execute command
            if '\n' not in command and not command.strip().endswith(':'):
                try:
                    # Try eval for simple expressions
                    result = eval(command, self.shell.user_ns)
                    if result is not None:
                        output = str(result) + "\n"
                    else:
                        output = ""
                except:
                    # Fall back to run_cell for complex commands
                    self.shell.run_cell(command)
                    output = captured_output.getvalue()
            else:
                self.shell.run_cell(command)
                output = captured_output.getvalue()

            # Clean and display output
            if output:
                clean_text = self._clean_ansi(output)
                self.root.after(0, lambda: self._update_term_display(clean_text))

        except Exception as e:
            error_msg = f"Error: {str(e)}\n"
            self.root.after(0, lambda: self._update_term_display(error_msg))
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            captured_output.close()

    def _show_terminal_output(self, output):
        # Clean ANSI escape codes
        import re
        clean_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
        self.root.after(0, lambda: self._update_term_display(clean_text))

    def _update_term_display(self, text):
        """Thread-safe display update"""
        self.term_display.config(state=tk.NORMAL)
        self.term_display.insert(tk.END, text)
        self.term_display.see(tk.END)
        self.term_display.config(state=tk.DISABLED)

    def _clean_ansi(self, text):
        """Remove ANSI escape sequences from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _handle_display(self, result):
        if result is not None:
            self._show_terminal_output(repr(result) + "\n")

    def _send_from_terminal(self, message):
        """Execute send message from terminal"""
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", message)
        self._send_message()

    # Add these methods for stdout redirection
    def _format_output(self, obj, include=None, exclude=None):
        """Format output without ANSI codes"""
        from IPython.core.formatters import format_display_data
        data = format_display_data(obj)
        return str(data['text/plain'])

    def write(self, text):
        self.root.after(0, lambda: self._update_term_display(text))

    def flush(self):
        pass
