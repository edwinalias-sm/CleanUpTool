import tkinter as tk
from tkinter import filedialog, messagebox
from eod_cleaner.cleaner import EODCleaner


class EODCleanupGUI:
    def __init__(self, root):
        self.cleaner = EODCleaner()
        self.root = root
        self.root.title("EOD Cleanup Tool")

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

    def select_root_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(folder, self.cleaner.archive_folder)

    def select_archive_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(self.cleaner.root_folder, folder)

    def run_scan(self):
        if not self.cleaner.root_folder:
            messagebox.showerror("Error", "Select a root folder first!")
            return
        runspec_files = self.cleaner.find_runspec_files()
        self.cleaner.extract_runspec_metadata(runspec_files)
        unused_eods = self.cleaner.list_unused_eods()
        self.cleaner.save_metadata(unused_eods)
        messagebox.showinfo("Success", "Scan completed and metadata saved.")

    def move_files(self):
        if not self.cleaner.archive_folder:
            messagebox.showerror("Error", "Select an archive folder first!")
            return
        self.cleaner.move_eods()
        messagebox.showinfo("Success", "Unused EODs moved.")


