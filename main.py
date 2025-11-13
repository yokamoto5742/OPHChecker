import tkinter as tk

from app.main_window import OPHCheckerGUI
from utils.config_manager import load_config
from utils.log_rotation import setup_logging

if __name__ == "__main__":
    config = load_config()
    setup_logging(config)

    root = tk.Tk()
    app = OPHCheckerGUI(root)
    root.mainloop()
