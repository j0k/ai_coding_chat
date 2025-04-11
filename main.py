import tkinter as tk
from gui.main_window import DeepSeekChatApp

def main():
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
