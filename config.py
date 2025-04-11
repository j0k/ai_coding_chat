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
    
import requests

class APIClient:
    def __init__(self, api_token, api_endpoint):
        self.api_token = api_token
        self.api_endpoint = api_endpoint

    def send_request(self, model, messages, temperature):
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e

    def parse_response(self, response):
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            raise ValueError("Invalid API response structure")
