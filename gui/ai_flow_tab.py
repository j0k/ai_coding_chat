import os
import json
import uuid
from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, messagebox, filedialog

class AIFlowTab:
    def __init__(self, parent, root, chat_panel, status_bar=None):
        self.parent = parent
        self.root = root
        self.chat_panel = chat_panel
        self.status_bar = status_bar

        self.flows = []
        self.current_flow = None
        self._callbacks = {}
        self._current_execution_id = None
        self._processing_flow = False
        self._pending_prompts = []
        self._abort_requested = False

        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self.load_flows()

    def set_status_bar(self, status_bar):
        self.status_bar = status_bar

    def _create_widgets(self):
        # Flow selection
        self.flow_selector_frame = ttk.Frame(self.frame)
        self.flow_selector_frame.pack(fill=tk.X, pady=5)

        # Add Save button next to Load
        self.save_btn = ttk.Button(
            self.flow_selector_frame,
            text="Save Flow",
            command=self._save_flow,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5)

        self.load_btn = ttk.Button(
            self.flow_selector_frame,
            text="Load Flow",
            command=self._load_flow_from_file
        )
        self.load_btn.pack(side=tk.RIGHT, padx=5)

        ttk.Label(self.flow_selector_frame, text="Select Flow:").pack(side=tk.LEFT, padx=5)
        self.flow_cbox = ttk.Combobox(self.flow_selector_frame, state="readonly")
        self.flow_cbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Add Title edit field
        self.title_frame = ttk.Frame(self.frame)
        self.title_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.title_frame, text="Flow Title:").pack(side=tk.LEFT, padx=5)
        self.title_entry = ttk.Entry(self.title_frame)
        self.title_entry.pack(fill=tk.X, expand=True, padx=5)
        self.title_entry.bind("<KeyRelease>", self._on_title_edit)

        # Delimiter controls
        self.delimiter_frame = ttk.Frame(self.frame)
        self.delimiter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.delimiter_frame, text="Prompt Delimiter:").pack(side=tk.LEFT)
        self.delimiter_entry = ttk.Entry(self.delimiter_frame, width=10)
        self.delimiter_entry.pack(side=tk.LEFT, padx=5)
        self.delimiter_entry.insert(0, "-----")

        # Flow preview and controls
        self.flow_controls_frame = ttk.Frame(self.frame)
        self.flow_controls_frame.pack(fill=tk.BOTH, expand=True)

        self.flow_preview = ScrolledText(self.flow_controls_frame, wrap=tk.WORD)
        self.flow_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        self.flow_preview.config(state=tk.NORMAL)

        self.check_btn = ttk.Button(
            self.flow_controls_frame,
            text="Check Flow",
            command=self._check_flow
        )
        self.check_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.run_btn = ttk.Button(
            self.flow_controls_frame,
            text="Run Flow",
            command=self._start_flow_execution
        )
        self.run_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.abort_btn = ttk.Button(
            self.flow_controls_frame,
            text="Abort",
            command=self._abort_flow,
            state=tk.DISABLED
        )
        self.abort_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.flow_cbox.bind("<<ComboboxSelected>>", self._on_flow_select)
        self.delimiter_entry.bind("<FocusOut>", self._update_flow_delimiter)

    def _on_title_edit(self, event=None):
        """Handle title changes"""
        if self.current_flow:
            self.current_flow["name"] = self.title_entry.get()
            self._pending_changes = True
            self.save_btn.config(state=tk.NORMAL)

    def _save_flow(self):
        """Save flow matching load schema"""
        if not self.current_flow:
            return

        try:
                # Parse current state
            flow_data = {
                "name": self.title_entry.get().strip(),
                "prompts": self._parse_raw_prompts(),
                "delimiter": self.delimiter_entry.get().strip(),
                "metadata": {
                    "created": self.current_flow.get("metadata", {}).get("created", datetime.now().isoformat()),
                    "modified": datetime.now().isoformat()
                }
            }

            # Validate required fields
            if not flow_data["name"]:
                raise ValueError("Flow must have a title")
            if not flow_data["prompts"]:
                raise ValueError("Flow must contain prompts")

            # Set default filename if new flow
            default_filename = f"{flow_data['name'].lower().replace(' ', '_')}.json"

            # Mirror load dialog style but for saving
            file_path = filedialog.asksaveasfilename(
                title="Save Flow As",
                initialfile=default_filename,
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                initialdir="ai_flows"
            )

            if not file_path:  # User cancelled
                return

            # Update filename in flow data
            flow_data["filename"] = os.path.basename(file_path)

            # Write to file
            with open(file_path, "w") as f:
                json.dump(flow_data, f, indent=2)

            # Update UI state
            self._update_flow_list(flow_data)
            self.status_bar.set_status(f"Saved: {flow_data['filename']}")
            self.save_btn.config(state=tk.DISABLED)
            self._pending_changes = False

        except Exception as e:
            messagebox.showerror("Save Error", f"Save failed: {str(e)}")

    def _parse_raw_prompts(self):
        """Parse the raw text editor content into prompt list format"""
        raw_text = self.flow_preview.get("1.0", tk.END).strip()
        delimiter = self.delimiter_entry.get().strip() or "-----"

        if not raw_text:
            return []

        # Split by delimiter and clean each section
        sections = [s.strip() for s in raw_text.split(delimiter) if s.strip()]
        prompts = []

        for section in sections:
            # Extract title (first line starting with #)
            lines = section.split('\n')
            title = None
            content_lines = []

            for line in lines:
                if line.startswith('#') and title is None:
                    title = line[1:].strip()
                else:
                    content_lines.append(line)

            # Clean and validate content
            content = '\n'.join(content_lines).strip()
            if not content:
                continue

            # Format matches the loaded structure
            if title:
                prompt_text = f"# {title}\n{content}"
            else:
                prompt_text = content

            prompts.append(prompt_text)

        return prompts

    def _update_flow_list(self, flow_data):
        """Refresh flow list after save"""
        # Update existing or add new
        existing = next((f for f in self.flows if f["filename"] == flow_data["filename"]), None)
        if existing:
            existing.update(flow_data)
        else:
            self.flows.append(flow_data)

        # Refresh combobox
        self.flow_cbox["values"] = [f["name"] for f in self.flows]
        self.flow_cbox.set(flow_data["name"])

    def _on_flow_select(self, event=None):
        """Load selected flow into editor"""
        flow_name = self.flow_cbox.get()
        self.current_flow = next((f for f in self.flows if f["name"] == flow_name), None)

        if self.current_flow:
            # Update title and delimiter
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, self.current_flow["name"])
            self.delimiter_entry.delete(0, tk.END)
            self.delimiter_entry.insert(0, self.current_flow.get("delimiter", "-----"))

            # Load prompts into editor
            self.flow_preview.config(state=tk.NORMAL)
            self.flow_preview.delete(1.0, tk.END)
            prompts = self.current_flow["prompts"]
            self.flow_preview.insert(tk.END, "\n" + self.current_flow["delimiter"] + "\n".join(prompts))
            self.flow_preview.config(state=tk.NORMAL)

            self.save_btn.config(state=tk.DISABLED)

    def load_flows(self):
        flow_dir = "ai_flows"
        try:
            if not os.path.exists(flow_dir):
                os.makedirs(flow_dir)
                return

            self.flows = []
            for filename in os.listdir(flow_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(flow_dir, filename), "r") as f:
                        flow = json.load(f)
                        if self._validate_flow(flow):
                            flow["filename"] = filename
                            self.flows.append(flow)

            self.flow_cbox["values"] = [flow["name"] for flow in self.flows]
            if self.flows:
                self.flow_cbox.current(0)
                self._on_flow_select()

        except Exception as e:
            messagebox.showerror("Flow Error", f"Failed to load flows: {str(e)}")

    def _validate_flow(self, flow):
        return all(key in flow for key in ["name", "prompts"])

    def _check_flow(self):
        """Check flow and update prompts if edited"""
        if not hasattr(self, 'current_flow'):
            return

        #import ipdb; ipdb.set_trace()

        # Get current editor content
        new_content = self.flow_preview.get("1.0", tk.END).strip()
        delimiter = self.delimiter_entry.get().strip() or "-----"

        # Parse and validate prompts
        prompts = [p.strip() for p in new_content.split(delimiter) if p.strip()]
        prompt_count = len(prompts)

        # Update status
        status = f"Flow contains {prompt_count} prompts"
        if hasattr(self, 'status_bar'):
            self.status_bar.set_status(status)
        else:
            messagebox.showinfo("Flow Check", status)

        # Only update current flow if changes exist
        if "\n".join(self.current_flow["prompts"]) != new_content:
            self._pending_changes = True
            self.current_flow["prompts"] = prompts
            self.current_flow["delimiter"] = delimiter

            # Visual feedback for unsaved changes
            if hasattr(self, 'save_btn'):
                self.save_btn.config(state=tk.NORMAL)

    def _on_flow_select(self, event=None):
        flow_name = self.flow_cbox.get()
        self.current_flow = next((f for f in self.flows if f["name"] == flow_name), None)
        if self.current_flow:
            self._update_flow_preview()

    def _update_flow_preview(self):
        self.flow_preview.config(state=tk.NORMAL)
        self.flow_preview.delete(1.0, tk.END)
        self.flow_preview.insert(tk.END, ("\n"+self.current_flow["delimiter"] + "\n").join(self.current_flow["prompts"]))
        self.flow_preview.config(state=tk.NORMAL)
        #import ipdb; ipdb.set_trace()
        self.delimiter_entry.delete(0, tk.END)
        self.delimiter_entry.insert(0, self.current_flow.get("delimiter", "-----"))

    def _update_flow_delimiter(self, event=None):
        if self.current_flow:
            self.current_flow["delimiter"] = self.delimiter_entry.get().strip()

    def _start_flow_execution(self):
        if self._processing_flow:
            return

        prompts = self._parse_flow_prompts()
        if not prompts:
            return

        self._processing_flow = True
        self._pending_prompts = prompts.copy()
        self.run_btn.config(state=tk.DISABLED, text="Running...")
        self.abort_btn.config(state=tk.NORMAL)
        self._execute_flow(prompts)

    def _parse_flow_prompts(self):
        delimiter = self.current_flow.get("delimiter", "-----")
        return self.current_flow["prompts"]
        #import ipdb; ipdb.set_trace()
        print([p.strip() for p in "\n".join(self.current_flow["prompts"]).split(delimiter) if p.strip()])
        return [p.strip() for p in "\n".join(self.current_flow["prompts"]).split(delimiter) if p.strip()]

    def _execute_flow(self, prompts):
        """New version with proper waiting mechanism"""
        if not prompts or not self._processing_flow:
            self._processing_flow = False
            self.run_btn.config(state=tk.NORMAL, text="Run Flow")
            self.abort_btn.config(state=tk.DISABLED)
            return

        # Store prompts and start processing
        self._pending_prompts = prompts
        self._process_next_prompt()

    def _process_next_prompt(self):
        if not self._processing_flow or self._abort_requested:
            self._cleanup_flow_execution()
            return

        if not self._pending_prompts:
            self._cleanup_flow_execution()
            return

        # Get current execution state from main window
        if self._is_processing_active():
            # If still processing, check again later
            self.root.after(200, self._process_next_prompt)
            return

        prompt = self._pending_prompts.pop(0)
        self._current_execution_id = str(uuid.uuid4())

        # Send prompt and register completion callback
        self._send_prompt_to_chat(prompt, self._on_prompt_complete)

    def _on_prompt_complete(self, success):
        """Callback when a prompt finishes processing"""
        if not self._processing_flow:
            return

        if success and self._pending_prompts:
            self._process_next_prompt()
        else:
            self._cleanup_flow_execution()

    def _is_processing_active(self):
        """Safely determine if a prompt is still being processed"""
        try:
            pass
            #print("_is_processing_active")
            #print(self.status_bar.progress_bar.cget('mode'))
        except Exception as e:
            pass

        try:
            # 1. First check the chat panel's send button state
            chat_processing = False
            if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'send_btn'):
                chat_processing = (str(self.chat_panel.send_btn['state']) == 'disabled')

            # 2. Then check status bar if available
            status_bar_processing = False
            status_bar = getattr(self, 'status_bar', None)
            if (status_bar is not None and
                hasattr(status_bar, 'progress_bar') and
                'mode' in status_bar.progress_bar.config()):
                status_bar_processing = (status_bar.progress_bar.cget('mode') == 'indeterminate')

            return chat_processing or status_bar_processing

        except Exception as e:
            print(f"Processing check error: {e}")
            # Default to True when uncertain to prevent overlapping executions
            return True


    def _send_prompt_to_chat(self, prompt, callback):
        """Modified to track completion"""
        print("_send_prompt_to_chat", prompt, callback )
        try:
            # Store callback with execution ID
            self._callbacks[self._current_execution_id] = callback

            # Monkey-patch the original send handler
            original_send = self.chat_panel._send_message

            def wrapped_send():
                original_send()
                # After sending, check for completion periodically
                self._monitor_completion()

            self.chat_panel._send_message = wrapped_send

            # Set up the prompt
            self.chat_panel.input.delete("1.0", tk.END)
            self.chat_panel.input.insert("1.0", prompt)
            self.chat_panel._send_message()

        except Exception as e:
            messagebox.showerror("Flow Error", f"Failed to send prompt: {str(e)}")
            self._cleanup_flow_execution()

    def _monitor_completion(self):
        """Check if current message processing has completed"""
        if not self._is_processing_active():
            # Get the callback and execute it
            callback = self._callbacks.pop(self._current_execution_id, None)
            if callback:
                callback(True)
        else:
            # Check again after 100ms
            self.root.after(100, self._monitor_completion)

    def _cleanup_flow_execution(self):
        """Reset execution state"""
        self._processing_flow = False
        self._abort_requested = False
        self._pending_prompts = []
        self._current_execution_id = None
        self.run_btn.config(state=tk.NORMAL, text="Run Flow")
        self.abort_btn.config(state=tk.DISABLED)


    def _abort_flow(self):
        """Comprehensive flow abortion handler"""
        # 1. Signal abortion
        self._abort_requested = True
        self._processing_flow = False

        # 2. Clear pending queue
        self._pending_prompts = []

        # 3. Reset UI states
        self.run_btn.config(state=tk.NORMAL, text="Run Flow")
        self.abort_btn.config(state=tk.DISABLED)

        # 4. Force-enable send button if stuck
        if self.chat_panel.send_btn['state'] == tk.DISABLED:
            self.chat_panel.enable_send_button()

        # 5. Stop progress indication
        if hasattr(self, 'status_bar'):
            self.status_bar.stop_progress()
            self.status_bar.set_status("Flow aborted by user")

    def _load_flow_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Flow File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                flow = json.load(f)

            if not self._validate_flow(flow):
                messagebox.showerror("Invalid Flow", "Flow must contain 'name' and 'prompts' fields")
                return

            # Check for existing flow with same name
            existing_names = [f["name"] for f in self.flows]
            if flow["name"] in existing_names:
                if not messagebox.askyesno("Duplicate Flow",
                                        f"Flow '{flow['name']}' already exists. Replace?"):
                    return
                # Remove existing flow
                self.flows = [f for f in self.flows if f["name"] != flow["name"]]

            # Add filename and add to flows
            flow["filename"] = os.path.basename(file_path)
            self.flows.append(flow)

            # Update UI
            self.flow_cbox["values"] = [f["name"] for f in self.flows]
            self.flow_cbox.set(flow["name"])
            self._on_flow_select()

            if hasattr(self, 'status_bar'):
                self.status_bar.set_status(f"Loaded flow: {flow['name']}")

        except Exception as e:
            messagebox.showerror("Load Error",
                               f"Failed to load flow file:\n{str(e)}")

    def _monitor_completion(self):
        """Periodically check if current prompt processing is complete"""
        if not self._processing_flow:  # Abort if flow was stopped
            return

        if not self._is_processing_active():  # Current prompt finished
            callback = self._callbacks.pop(self._current_execution_id, None)
            if callback:
                callback(True)  # Notify success
        else:  # Still processing, check again later
            self.root.after(100, self._monitor_completion)  # Re-check in 100ms
