import configparser
from tkinter import messagebox

def load_config():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        return {
            'api_token': config['DEFAULT']['API_TOKEN'],
            'api_endpoint': config['DEFAULT'].get(
                'API_ENDPOINT',
                'https://api.deepseek.com/v1/chat/completions'
            )
        }
    except (KeyError, FileNotFoundError) as e:
        messagebox.showerror("Error", f"Configuration error: {str(e)}")
        return None
