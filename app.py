import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import configparser
import requests
import json

class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek Chat")
        self.root.geometry("1000x750")

        # Initialize conversation tracking
        self.conversation_history = []
        self.question_indices = []
        self.available_models = [
            'deepseek-chat',
            'deepseek-coder-33b-instruct',
            'deepseek-math-7b-instruct',
            'deepseek-reasoner'
        ]

        # Load configuration
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            self.api_token = self.config['DEFAULT']['API_TOKEN']
            self.api_endpoint = self.config['DEFAULT'].get('API_ENDPOINT', 'https://api.deepseek.com/v1/chat/completions')
        except (KeyError, FileNotFoundError):
            messagebox.showerror("Error", "Missing or invalid config file")
            self.root.destroy()
            return

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Configure grid layout
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=150)
        self.root.grid_columnconfigure(1, weight=1)

        # Toolbar Frame
        self.toolbar_frame = ttk.Frame(self.root)
        self.toolbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        # Toolbar Elements
        # Export/Load buttons
        self.export_btn = ttk.Button(self.toolbar_frame, text="Export Session", command=self.export_session)
        self.export_btn.pack(side=tk.LEFT, padx=2)
        self.load_btn = ttk.Button(self.toolbar_frame, text="Load Session", command=self.load_session)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        # Font Selection
        ttk.Label(self.toolbar_frame, text="Font:").pack(side=tk.LEFT, padx=(10, 2))
        self.font_var = tk.StringVar(value="Arial")
        self.font_combo = ttk.Combobox(
            self.toolbar_frame,
            textvariable=self.font_var,
            values=["Arial", "Courier New", "Times New Roman"],
            state="readonly",
            width=15
        )
        self.font_combo.pack(side=tk.LEFT)
        self.font_combo.bind("<<ComboboxSelected>>", self.change_font)

        # Context Checkbox
        self.use_context_var = tk.BooleanVar()
        self.context_check = ttk.Checkbutton(
            self.toolbar_frame,
            text="Use Context",
            variable=self.use_context_var,
            onvalue=True,
            offvalue=False
        )
        self.context_check.pack(side=tk.LEFT, padx=10)

        # Navigation Panel
        self.nav_frame = ttk.Frame(self.root)
        self.nav_frame.grid(row=1, column=0, sticky="nswe")

        # Question listbox with scrollbar
        self.nav_listbox = tk.Listbox(self.nav_frame)
        self.nav_scroll = ttk.Scrollbar(self.nav_frame, orient="vertical", command=self.nav_listbox.yview)
        self.nav_listbox.configure(yscrollcommand=self.nav_scroll.set)
        self.nav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.nav_listbox.bind('<<ListboxSelect>>', self.on_nav_select)

        # Chat Area
        self.chat_frame = ttk.Frame(self.root)
        self.chat_frame.grid(row=1, column=1, sticky="nswe")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Chat history display
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, state='normal',
            font=('Arial', 10), spacing3=5
        )
        self.chat_history.tag_config('user', foreground='#006400')
        self.chat_history.tag_config('assistant', foreground='#00008B')
        self.chat_history.tag_config('system', foreground='#8B0000')
        self.chat_history.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Input frame
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        # User input with scrollbar
        self.user_input = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, height=3,
            font=('Arial', 10), undo=True
        )
        self.user_input.grid(row=0, column=0, sticky="ew")
        self.user_input.bind("<Return>", self.handle_enter_key)

        # Send button
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=5, sticky="e")

        # Control panel
        control_frame = ttk.Frame(self.chat_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Model selection
        ttk.Label(control_frame, text="Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value=self.available_models[0])
        self.model_select = ttk.Combobox(
            control_frame, textvariable=self.model_var,
            values=self.available_models, state='readonly', width=25
        )
        self.model_select.pack(side=tk.LEFT, padx=5)

        # Temperature control
        ttk.Label(control_frame, text="Temperature:").pack(side=tk.LEFT, padx=5)
        self.temperature = tk.DoubleVar(value=0.7)
        self.temp_slider = ttk.Scale(
            control_frame, from_=0, to=1, variable=self.temperature,
            orient="horizontal", command=lambda _: self.update_temp_label()
        )
        self.temp_slider.pack(side=tk.LEFT, padx=5)
        self.temp_label = ttk.Label(control_frame, text="0.7", width=4)
        self.temp_label.pack(side=tk.LEFT, padx=5)

    def handle_enter_key(self, event):
        if event.state == 0:
            self.send_message()
            return "break"
        return None

    def update_temp_label(self):
        self.temp_label.config(text=f"{self.temperature.get():.1f}")

    def change_font(self, event=None):
        new_font = self.font_var.get()
        self.chat_history.config(font=(new_font, 10))
        self.user_input.config(font=(new_font, 10))

    def export_session(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w') as f:
                json.dump(self.conversation_history, f)
            messagebox.showinfo("Success", "Session exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def load_session(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                self.conversation_history = json.load(f)
            self.question_indices = [
                i for i, entry in enumerate(self.conversation_history)
                if entry['sender'] == 'user'
            ]
            self.nav_listbox.delete(0, tk.END)
            for idx, entry_idx in enumerate(self.question_indices, start=1):
                msg = self.conversation_history[entry_idx]['message']
                self.nav_listbox.insert(tk.END, f"{idx}. {msg[:20]}...")
            self.display_conversation_up_to(len(self.conversation_history)-1)
            messagebox.showinfo("Success", "Session loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Load failed: {str(e)}")

    def send_message(self):
        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message:
            return

        self.user_input.delete("1.0", tk.END)
        self.conversation_history.append({'sender': 'user', 'message': user_message})
        self.question_indices.append(len(self.conversation_history)-1)
        self.nav_listbox.insert(tk.END, f"{len(self.question_indices)}. {user_message[:20]}...")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            # Prepare messages payload
            if self.use_context_var.get():
                messages = [
                    {"role": entry['sender'], "content": entry['message']}
                    for entry in self.conversation_history
                    if entry['sender'] in ['user', 'assistant']
                ]
            else:
                messages = [{"role": "user", "content": user_message}]

            payload = {
                "model": self.model_var.get(),
                "messages": messages,
                "temperature": self.temperature.get()
            }

            response = requests.post(self.api_endpoint, headers=headers, json=payload)

            if response.status_code == 200:
                ai_message = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({'sender': 'assistant', 'message': ai_message})
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                self.conversation_history.append({'sender': 'system', 'message': error_msg})

            self.display_conversation_up_to(len(self.conversation_history)-1)
            self.nav_listbox.selection_clear(0, tk.END)
            self.nav_listbox.selection_set(tk.END)
            self.nav_listbox.see(tk.END)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.conversation_history.append({'sender': 'system', 'message': error_msg})
            self.display_conversation_up_to(len(self.conversation_history)-1)

    def on_nav_select(self, event):
        selected = self.nav_listbox.curselection()
        if selected:
            idx = selected[0]
            if idx < len(self.question_indices):
                user_msg_idx = self.question_indices[idx]
                end_idx = user_msg_idx + 1
                if end_idx >= len(self.conversation_history):
                    end_idx = len(self.conversation_history) - 1
                self.display_conversation_up_to(end_idx)

    def display_conversation_up_to(self, end_idx):
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, tk.END)
        for i in range(end_idx + 1):
            if i >= len(self.conversation_history):
                break
            entry = self.conversation_history[i]
            tag = entry['sender']
            self.chat_history.insert(tk.END, f"{entry['sender'].title()}: {entry['message']}\n\n", tag)
        self.chat_history.config(state='normal')
        self.chat_history.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()
    
