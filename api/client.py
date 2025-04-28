import requests
import threading

class APIClient:
    def __init__(self, api_token, api_endpoint):
        self.api_token = api_token
        self.api_endpoint = api_endpoint
        self._lock = threading.Lock()

    def send_request(self, model, messages, temperature, timeout_enabled=True):
        timeout = 15 if timeout_enabled else None
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        print("\n\n",model, payload)

        with self._lock:  # Ensure thread-safe API calls
            try:
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=timeout
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
