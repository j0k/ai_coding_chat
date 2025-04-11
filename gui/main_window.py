import json
import tkinter as tk
from tkinter import ttk, messagebox
from api.client import APIClient  # Changed import path
from gui.navigation import NavigationPanel  # Changed import path
from gui.chat import ChatPanel
from gui.toolbar import Toolbar
from gui.status_bar import StatusBar
from config import load_config
from utils.helpers import export_session, load_session, format_error

class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        if not self.config:
            root.destroy()
            return
            
        self.api_client = APIClient(
            self.config['api_token'],
            self.config['api_endpoint']
        )
        
        self.conversation_history = []
        self.question_indices = []
        
        self._init_ui()
        self._bind_events()
        self._setup_state()
        self.navigation.on_context_update(self._handle_context_update)
        self.toolbar.on_timeout_change(self.handle_timeout_change)
        self.timeout_enabled = False  # Default state

    def _init_ui(self):
        self.root.title("DeepSeek Chat")
        self.root.geometry("1000x750")
        
        # Initialize components
        self.toolbar = Toolbar(self.root)
        self.navigation = NavigationPanel(self.root)
        self.chat = ChatPanel(self.root)
        self.status_bar = StatusBar(self.root)
        
        # Configure grid layout
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=150)
        self.root.grid_columnconfigure(1, weight=1)

    def _bind_events(self):
        # Toolbar events
        self.toolbar.on_export(self.handle_export)
        self.toolbar.on_load(self.handle_load)
        self.toolbar.on_font_change(lambda font: self.chat.update_font(font))
        self.toolbar.on_temp_change(self.handle_temp_change)
        
        # Navigation events
        self.navigation.on_select(self.handle_nav_select)
        
        # Chat events
        self.chat.on_send(self.handle_message_send)

    def _setup_state(self):
        self.temperature = 0.7
        self.current_font = "Arial"

    def handle_message_send(self, message):
        self.status_bar.start_progress()
        self.status_bar.set_status("Processing...")
        
        try:
            # Add user message
            self._add_conversation_entry('user', message)
            
            # Prepare API request
            messages = self._prepare_messages()
            response = self.api_client.send_request(
                self.toolbar.model_var.get(),
                messages,
                self.temperature,
                timeout_enabled=self.timeout_enabled
            )
            
            # Add assistant response
            ai_message = self.api_client.parse_response(response)
            self._add_conversation_entry('assistant', ai_message)
            
            self.status_bar.set_status("Response received")
            
        except Exception as e:
            error_msg = format_error(e)
            self._add_conversation_entry('system', error_msg)
            self.status_bar.set_status(f"Error: {error_msg[:30]}...")
            
        finally:
            self.status_bar.stop_progress()
            self.chat.history.see(tk.END)

    def handle_timeout_change(self, enabled):
        """Update timeout state"""
        self.timeout_enabled = enabled
        
    def _handle_context_update(self, entry_idx, include_state):
        """Update conversation history from navigation panel changes"""
        try:
            self.conversation_history[entry_idx]['include_in_context'] = include_state
            # Auto-update corresponding response if exists
            if entry_idx + 1 < len(self.conversation_history):
                self.conversation_history[entry_idx+1]['include_in_context'] = include_state
        except IndexError:
            pass

    def _add_conversation_entry(self, sender, message):
        entry = {
            'sender': sender,
            'message': message,
            'include_in_context': True
        }
        self.conversation_history.append(entry)
        
        if sender == 'user':
            self.question_indices.append(len(self.conversation_history)-1)
            self.navigation.add_message(
                len(self.question_indices),
                len(self.conversation_history)-1,
                message
            )
            
        self._update_chat_display()

    def _prepare_messages(self):
        if self.toolbar.use_context_var.get():
            return [
                {"role": entry['sender'], "content": entry['message']}
                for entry in self.conversation_history
                if entry['include_in_context'] 
                and entry['sender'] in ['user', 'assistant']
            ]
        return [{"role": "user", "content": self.conversation_history[-1]['message']}]

    def _update_chat_display(self):
        self.chat.history.config(state=tk.NORMAL)
        self.chat.history.delete(1.0, tk.END)
        
        for entry in self.conversation_history:
            tag = entry['sender']
            self.chat.history.insert(
                tk.END, 
                f"{entry['sender'].title()}: {entry['message']}\n\n", 
                tag
            )
            
        self.chat.history.config(state=tk.NORMAL)

    def handle_export(self):
        self.status_bar.start_progress()
        if export_session(self.conversation_history):
            self.status_bar.set_status("Session exported successfully")
        else:
            self.status_bar.set_status("Export failed")
        self.status_bar.stop_progress()

    def handle_load(self):
        self.status_bar.start_progress()
        if data := load_session():
            self.conversation_history = data
            self.question_indices = [
                i for i, entry in enumerate(self.conversation_history) 
                if entry['sender'] == 'user'
            ]
            self.navigation.clear()
            for idx, entry_idx in enumerate(self.question_indices, 1):
                self.navigation.add_message(
                    idx,
                    entry_idx,
                    self.conversation_history[entry_idx]['message'],
                    self.conversation_history[entry_idx]['include_in_context']
                )
            self._update_chat_display()
            self.status_bar.set_status("Session loaded successfully")
        self.status_bar.stop_progress()

    def handle_nav_select(self, entry_idx):
        end_idx = entry_idx + 1
        if end_idx >= len(self.conversation_history):
            end_idx = len(self.conversation_history) - 1
        
        self.chat.history.see(f"{end_idx + 1}.0")
        self.chat.history.tag_add(tk.SEL, f"{entry_idx}.0", f"{end_idx}.0")

    def handle_temp_change(self, temp):
        self.temperature = temp

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()
