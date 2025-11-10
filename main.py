import tkinter as tk

from app.main_window import OPHCheckerGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = OPHCheckerGUI(root)
    root.mainloop()
