import tkinter as tk
from gui.main_window import DeepSeekChatApp
import sys
import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))
    
def main():
    root = tk.Tk()
    root.iconbitmap("logo.ico")
    app = DeepSeekChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
