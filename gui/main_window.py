import time
import uuid
from api.client import APIClient
from gui.navigation import NavigationPanel
from gui.chat import ChatPanel
from gui.toolbar import Toolbar
from gui.status_bar import StatusBar
from gui.memo_panel import MemoPanel
from config import load_config
from utils.helpers import export_session, load_session, format_error
import queue
import tkinter as tk
import threading

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
        self.execution_times = {}
        self.message_queue = queue.Queue()

        self._init_ui()
        self._setup_threading()
        self._bind_events()
        self._connect_components()
        self._setup_state()

    def _init_ui(self):
        self.root.title("AI Coding Chat")
        self.root.geometry("1200x750")

        # Configure grid layout
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=150)  # Navigation
        self.root.grid_columnconfigure(1, weight=1)               # Chat
        self.root.grid_columnconfigure(2, weight=0, minsize=50)  # Memo

        # Initialize components
        self.toolbar = Toolbar(self.root)
        self.navigation = NavigationPanel(self.root)
        self.chat = ChatPanel(self.root)
        self.memo_panel = MemoPanel(self.root, self.chat, self.root)
        self.status_bar = StatusBar(self.root)
        self.memo_panel.ai_flow_tab.set_status_bar(self.status_bar)

        # Grid placement
        self.toolbar.frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.navigation.frame.grid(row=1, column=0, sticky="nswe")
        self.chat.frame.grid(row=1, column=1, sticky="nswe")
        #self.memo_panel.frame.grid(row=1, column=2, sticky="nswe")
        self.memo_panel.frame.grid(row=1, column=2, sticky="ns")
        self.status_bar.frame.grid(row=2, column=0, columnspan=3, sticky="ew")

    def _setup_threading(self):
        self.root.after(100, self._process_message_queue)

    def _process_message_queue(self):
        try:
            while True:
                callback = self.message_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_message_queue)

    def _bind_events(self):
        # Toolbar events
        self.toolbar.on_export(self.handle_export)
        self.toolbar.on_load(self.handle_load)
        self.toolbar.on_font_change(lambda font: self.chat.update_font(font))
        self.toolbar.on_temp_change(self.handle_temp_change)
        self.toolbar.on_timeout_change(self.handle_timeout_change)

        # Navigation events
        self.navigation.on_context_update(self._handle_context_update)
        self.navigation.on_select(self.handle_nav_select)

        # Chat events
        self.chat.on_send(self.handle_message_send)

    def _send_message_async(self, message, user_message_id):
        """Handle the async message sending and response processing"""
        try:
            start_time = time.time()

            # Prepare messages including context if enabled
            messages = self._prepare_messages(user_message_id)

            # Make API request
            response = self.api_client.send_request(
                model=self.toolbar.model_var.get(),
                messages=messages,
                temperature=self.temperature,
                timeout_enabled=self.timeout_enabled
            )

            execution_time = time.time() - start_time
            ai_message = self.api_client.parse_response(response)

            # Update UI in main thread
            self.message_queue.put(lambda: (
                # Add AI response linked to the user message
                self._add_conversation_entry(
                    sender='assistant',
                    message=ai_message,
                    parent_id=user_message_id
                ),
                # Update execution time for the original user message
                self._update_execution_time(user_message_id, execution_time),
                self.status_bar.set_status("Response received"),
                self.chat.history.see(tk.END)
            ))

        except Exception as e:
            error_msg = format_error(e)
            self.message_queue.put(lambda: (
                self._add_conversation_entry('system', error_msg),
                self.status_bar.set_status(f"Error: {error_msg[:30]}...")
            ))

        finally:
            self.message_queue.put(self.status_bar.stop_progress)
            self.message_queue.put(self.chat.enable_send_button)

    def _update_execution_time(self, user_entry_id, duration):
        """Update execution time for a specific user message"""
        try:
            # Find the user message entry
            user_entry = next(
                entry for entry in self.conversation_history
                if entry['entry_id'] == user_entry_id
                and entry['sender'] == 'user'
            )

            # Update both the data model and UI
            user_entry['_exec_time'] = duration
            self.navigation.update_badge(user_entry_id, f"{duration:.1f}s")

        except StopIteration:
            self.status_bar.set_status(f"Couldn't update time for {user_entry_id[:6]}...")

    def _handle_context_update(self, entry_id, include_state):
        """Update context inclusion state for a message and its response"""
        try:
            # Find the user message entry
            user_entry = next(
                entry for entry in self.conversation_history
                if entry['entry_id'] == entry_id and entry['sender'] == 'user'
            )
            user_entry['include_in_context'] = include_state

            # Find and update corresponding assistant response
            response_entry = next(
                (entry for entry in self.conversation_history
                 if entry.get('parent_id') == entry_id),
                None
            )

            if response_entry:
                response_entry['include_in_context'] = include_state
                self.status_bar.set_status(f"Updated context for message {entry_id[:6]}...")
            else:
                self.status_bar.set_status(f"Context updated - no response yet")

            # Refresh chat display to show changes
            self._update_chat_display()

        except StopIteration:
            self.status_bar.set_status(f"⚠️ Context update failed: Message {entry_id[:6]}... not found")
        except Exception as e:
            self.status_bar.set_status(f"Critical context error: {str(e)[:50]}")
            self._add_conversation_entry('system', f'Context update failed: {str(e)}')

    def handle_nav_select(self, selected_entry_id):
        """Handle navigation panel click with precise scrolling"""
        try:
            # Find the message index by entry_id
            message_index = next(
                i for i, entry in enumerate(self.conversation_history)
                if entry.get('entry_id') == selected_entry_id
            )

            # Verify we have position data for this message
            if message_index >= len(self.message_positions):
                self.status_bar.set_status("Refreshing message positions...")
                self._update_chat_display()  # Regenerate position data
                message_index = next(
                    i for i, entry in enumerate(self.conversation_history)
                    if entry.get('entry_id') == selected_entry_id
                )

            start_pos, end_pos = self.message_positions[message_index]

            # Scroll to message and highlight
            self.chat.history.see(start_pos)
            self.chat.history.tag_remove('highlight', 1.0, tk.END)
            self.chat.history.tag_add('highlight', start_pos, end_pos)

            # Remove highlight after 2 seconds
            self.root.after(2000, lambda: (
                self.chat.history.tag_remove('highlight', start_pos, end_pos)
            ))

        except StopIteration:
            self.status_bar.set_status("Message not found in history")
        except IndexError:
            self.status_bar.set_status("Position data mismatch - full refresh needed")
            self._update_chat_display()
        except Exception as e:
            self.status_bar.set_status(f"Navigation error: {str(e)[:50]}")

    def _connect_components(self):
        """Connect cross-component callbacks"""
        self.toolbar.on_toggle_memo(lambda : self.memo_panel.toggle_visibility())

    def _setup_state(self):
        self.temperature = 0.7
        self.timeout_enabled = False
        self.current_font = "Monaco"

    def handle_message_send(self, message):
        self.status_bar.start_progress()
        self.status_bar.set_status("Processing...")
        #self.chat.disable_send_button()
        self.chat.send_btn.config(state=tk.DISABLED)

        start_time = time.time()  # Add import time at top

        # Add to conversation entry with timestamp
        # entry_idx = len(self.conversation_history)
        # self.conversation_history.append({
        #     'sender': 'user',
        #     'message': message,
        #     'include_in_context': True,
        #     'timestamp': start_time  # New field
        # })

        # Add user message to history and get its ID
        user_message_id = self._add_conversation_entry(
            sender='user',
            message=message
        )

        # Start async processing
        threading.Thread(
            target=self._send_message_async,
            args=(message, user_message_id),  # Pass the message ID
            daemon=True
        ).start()

        # Run API request in separate thread

        # threading.Thread(
        #     target=self._send_message_async,
        #     args=(message,),
        #     daemon=True
        # ).start()

    def handle_timeout_change(self, enabled):
        """Update timeout state"""
        self.timeout_enabled = enabled

    def _add_conversation_entry(self, sender, message, parent_id=None):
        """Add new message to conversation with proper navigation linking"""
        entry_id = str(uuid.uuid4())
        entry = {
            'entry_id': entry_id,
            'sender': sender,
            'message': message,
            'include_in_context': True,
            'timestamp': time.time(),
            'parent_id': parent_id  # Link responses to their questions
        }
        self.conversation_history.append(entry)

        if sender == 'user':
            self.question_indices.append(len(self.conversation_history)-1)

            self.navigation.add_message(
                len(self.question_indices),
                entry_id,
                message,
                checked=True
            )

        self._update_chat_display()
        return entry_id

    def _prepare_messages(self, current_message_id):
        #if self.toolbar.use_context_var.get():
        #    return [
        #        {"role": entry['sender'], "content": entry['message']}
        #         for entry in self.conversation_history
        #         if entry['include_in_context']
        #         and entry['sender'] in ['user', 'assistant']
        #         and entry.get('entry_id') <= entry_id  # Only include previous messages
        #     ]
        # return [{"role": "user", "content": self.conversation_history[-1]['message']}]
        #
        """Prepare the message history for API request, respecting context settings"""
        messages = []

        #if not self.toolbar.use_context_var.get():
            # Context disabled - send only the last user message
            #last_user_msg = next(
            #    (msg for msg in reversed(self.conversation_history)
            #    if msg['sender'] == 'user' and msg['entry_id'] == current_message_id
            #)
            #return [{"role": "user", "content": last_user_msg['message']}]

        # Context enabled - build conversation history
        for entry in self.conversation_history:
            # Skip if not included in context
            if not entry['include_in_context']:
                continue

            # Only include messages that came before current one
            if 'entry_id' in entry and entry['entry_id'] > current_message_id:
                pass

            # Skip system messages in context
            if entry['sender'] not in ['user', 'assistant']:
                continue

            # Add valid messages to context
            messages.append({
                "role": entry['sender'],
                "content": entry['message']
            })

            # Stop if we've reached the current message
            if 'entry_id' in entry and entry['entry_id'] == current_message_id:
                break

        # Ensure we have at least the current message
        if not messages or messages[-1]['role'] != 'user':
            current_msg = next(
                msg for msg in self.conversation_history
                if msg['entry_id'] == current_message_id
            )
            messages.append({"role": "user", "content": current_msg['message']})

        return messages

    def _update_chat_display(self):
        self.chat.history.config(state=tk.NORMAL)
        self.chat.history.delete(1.0, tk.END)
        self.message_positions = []  # Reset positions

        for idx, entry in enumerate(self.conversation_history):
            # Record start position
            start_idx = self.chat.history.index(tk.INSERT)

            # Insert message as before
            tag = entry['sender']
            self.chat.history.insert(
                tk.END,
                f"{entry['sender'].title()}: {entry['message']}\n\n",
                tag
            )

            # Record end position
            end_idx = self.chat.history.index(tk.INSERT)
            self.message_positions.append((start_idx, end_idx))

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
                entry = self.conversation_history[entry_idx]
                exec_time = entry.get('_exec_time', "N/A")
                self.navigation.add_message(
                    idx,
                    entry.get('entry_id', str(uuid.uuid4())),
                    entry['message'],
                    entry.get('include_in_context', True),
                    execution_time=exec_time
                )

            self._update_chat_display()
            self.status_bar.set_status("Session loaded successfully")
        self.status_bar.stop_progress()

    def handle_temp_change(self, temp):
        self.temperature = temp


if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()
