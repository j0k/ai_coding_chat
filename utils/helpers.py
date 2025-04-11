import requests
import json
from tkinter import messagebox, filedialog

def export_session(conversation_history):
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return False
            
        with open(file_path, 'w') as f:
            json.dump([{
                'sender': entry['sender'],
                'message': entry['message'],
                'include_in_context': entry.get('include_in_context', True)
            } for entry in conversation_history], f)
            
        return True
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export session: {str(e)}")
        return False

def load_session():
    try:
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return None
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Backward compatibility for old sessions
        for entry in data:
            if 'include_in_context' not in entry:
                entry['include_in_context'] = True
                
        return data
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to load session: {str(e)}")
        return None

def format_error(error):
    """Convert exceptions to user-friendly messages"""
    if isinstance(error, requests.exceptions.RequestException):
        return "Network error: Failed to connect to API server"
    elif isinstance(error, json.JSONDecodeError):
        return "API Error: Invalid response format"
    elif isinstance(error, KeyError):
        return "API Error: Unexpected response structure"
    return f"Error: {str(error)}"

def validate_message(text):
    """Clean and validate user input"""
    cleaned = text.strip()
    if len(cleaned) < 2:
        return None
    return cleaned[:2000]  # Limit to 2000 characters

def format_message_preview(message):
    """Create truncated preview for navigation panel"""
    return (message[:35] + '...') if len(message) > 35 else message
