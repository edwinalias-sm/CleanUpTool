import tkinter as tk
from eod_cleaner.eod_cleanup_gui import EODCleanupGUI


if __name__ == "__main__":
    root = tk.Tk()
    app = EODCleanupGUI(root)
    root.mainloop()
