import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar
from eod_cleaner.cleaner import EODCleaner
import logging


class EODCleanupGUI:
    def __init__(self, root):
        self.cleaner = EODCleaner()
        self.root = root
        self.root.title("EOD Cleanup Tool")
        self.root.geometry("800x600")

        tk.Label(root, text="Select Root Folder").pack()
        self.root_folder_btn = tk.Button(
            root, text="Browse", command=self.select_root_folder
        )
        self.root_folder_btn.pack()

        tk.Label(root, text="Select Archive Folder").pack()
        self.archive_folder_btn = tk.Button(
            root, text="Browse", command=self.select_archive_folder
        )
        self.archive_folder_btn.pack()

        self.scan_btn = tk.Button(root, text="Run Dry Scan", command=self.run_scan)
        self.scan_btn.pack()

        self.move_btn = tk.Button(
            root, text="Move Unused EODs", command=self.move_files
        )
        self.move_btn.pack()

        self.progress = Progressbar(
            root, orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger()
        self.logger.addHandler(TextHandler(self.log_text))

    def select_root_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(folder, self.cleaner.archive_folder or "")

    def select_archive_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(self.cleaner.root_folder or "", folder)

    def run_scan(self):
        if not self.cleaner.root_folder:
            messagebox.showerror("Error", "Select a root folder first!")
            return
        self.progress.start()
        self.root.after(100, self._run_scan)

    def _run_scan(self):
        runspec_files = self.cleaner.find_runspec_files()
        self.cleaner.extract_runspec_metadata(runspec_files)
        unused_eods = self.cleaner.list_unused_eods()
        self.cleaner.save_metadata(unused_eods)
        self.progress.stop()
        messagebox.showinfo("Success", "Scan completed and metadata saved.")

    def move_files(self):
        if not self.cleaner.archive_folder:
            messagebox.showerror("Error", "Select an archive folder first!")
            return
        self.progress.start()
        self.root.after(100, self._move_files)

    def _move_files(self):
        self.cleaner.move_eods()
        self.progress.stop()
        messagebox.showinfo("Success", "Unused EODs moved.")


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.yview(tk.END)

        self.text_widget.after(0, append)


if __name__ == "__main__":
    root = tk.Tk()
    app = EODCleanupGUI(root)
    root.mainloop()
