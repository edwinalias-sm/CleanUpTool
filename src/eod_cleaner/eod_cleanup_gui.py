import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar, Combobox, Treeview, Style
from eod_cleaner.cleaner import EODCleaner
import logging


class EODCleanupGUI:
    def __init__(self, root):
        self.cleaner = EODCleaner()
        self.root = root
        self.root.title("EOD Cleanup Tool")
        self.root.geometry("800x600")

        # Create a frame for the buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Label(button_frame, text="Select Root Folder").grid(
            row=0, column=0, padx=5, pady=5
        )
        self.root_folder_btn = tk.Button(
            button_frame, text="Browse", command=self.select_root_folder
        )
        self.root_folder_btn.grid(row=0, column=1, padx=5, pady=5)

        self.scan_btn = tk.Button(
            button_frame, text="Run Dry Scan", command=self.run_scan
        )
        self.scan_btn.grid(row=0, column=2, padx=5, pady=5)

        tk.Label(button_frame, text="Select Archive Folder").grid(
            row=1, column=0, padx=5, pady=5
        )
        self.archive_folder_btn = tk.Button(
            button_frame, text="Browse", command=self.select_archive_folder
        )
        self.archive_folder_btn.grid(row=1, column=1, padx=5, pady=5)

        self.move_btn = tk.Button(
            button_frame, text="Move Unused EODs", command=self.move_files
        )
        self.move_btn.grid(row=1, column=2, padx=5, pady=5)

        tk.Label(button_frame, text="Log Level").grid(row=2, column=0, padx=5, pady=5)
        self.log_level = Combobox(
            button_frame, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self.log_level.current(1)  # Set default to INFO
        self.log_level.grid(row=2, column=1, padx=5, pady=5)
        self.log_level.bind("<<ComboboxSelected>>", self.set_log_level)

        self.progress = Progressbar(
            root, orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.tree = Treeview(
            self.tree_frame,
            columns=(
                "File Path",
                "File Name",
                "Creation Date",
                "Status",
                "Runspec File",
            ),
            show="headings",
        )
        self.tree.heading("File Path", text="File Path")
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Creation Date", text="Creation Date")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Runspec File", text="Runspec File")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.filter_var = tk.StringVar()
        self.filter_var.set("All")
        self.filter_menu = Combobox(
            root, textvariable=self.filter_var, values=["All", "Used", "Unused"]
        )
        self.filter_menu.pack(pady=5)
        self.filter_menu.bind("<<ComboboxSelected>>", self.filter_tree)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger()
        self.logger.addHandler(TextHandler(self.log_text))

    def set_log_level(self, event):
        level = self.log_level.get()
        self.logger.setLevel(getattr(logging, level))
        self.logger.info(f"Log level set to {level}")

    def select_root_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(folder, self.cleaner.archive_folder or "")
            self.logger.info(f"Root folder selected: {folder}")

    def select_archive_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.cleaner.set_folders(self.cleaner.root_folder or "", folder)
            self.logger.info(f"Archive folder selected: {folder}")

    def select_metadata_path(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")]
        )
        if file_path:
            self.cleaner.metadata_file = file_path
            self.logger.info(f"Metadata save path selected: {file_path}")

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
        self.logger.info("Scan completed and metadata saved.")
        messagebox.showinfo("Success", "Scan completed and metadata saved.")
        self.display_results(unused_eods)

    def display_results(self, eods):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for eod in eods:
            self.tree.insert("", "end", values=eod)

    def filter_tree(self, event):
        filter_value = self.filter_var.get()
        for row in self.tree.get_children():
            self.tree.delete(row)
        eods = self.cleaner.list_unused_eods()
        for eod in eods:
            if filter_value == "All" or eod[3] == filter_value:
                self.tree.insert("", "end", values=eod)

    def move_files(self):
        if not self.cleaner.archive_folder:
            messagebox.showerror("Error", "Select an archive folder first!")
            return
        if messagebox.askyesno(
            "Confirm Move",
            "Are you sure you want to move unused EODs? This operation is critical and risky.",
        ):
            self.progress.start()
            self.root.after(100, self._move_files)

    def _move_files(self):
        self.cleaner.move_eods()
        self.progress.stop()
        self.logger.info("Unused EODs moved.")
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
