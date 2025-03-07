import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import (
    Progressbar,
    Combobox,
    Treeview,
    Style,
    Button,
    Label,
    Frame,
    Checkbutton,
)
from datetime import datetime
from eod_cleaner.cleaner import EODCleaner
import logging
import threading


class EODCleanupGUI:
    def __init__(self, root):
        self.cleaner = EODCleaner()
        self.root = root
        self.root.title("EOD Cleanup Tool")
        self.root.geometry("850x600")

        self.use_threading = tk.BooleanVar(value=True)

        self.setup_ui()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger()
        self.logger.addHandler(TextHandler(self.log_text))

    def setup_ui(self):
        main_frame = Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Folder Selection
        folder_frame = Frame(main_frame)
        folder_frame.pack(pady=10, fill=tk.X)

        Label(folder_frame, text="Root Folder:").grid(row=0, column=0, padx=5, pady=5)
        Button(folder_frame, text="Browse", command=self.select_root_folder).grid(
            row=0, column=1, padx=5, pady=5
        )

        Label(folder_frame, text="Archive Folder:").grid(
            row=1, column=0, padx=5, pady=5
        )
        Button(folder_frame, text="Browse", command=self.select_archive_folder).grid(
            row=1, column=1, padx=5, pady=5
        )

        # Buttons
        action_frame = Frame(main_frame)
        action_frame.pack(pady=10, fill=tk.X)

        Button(action_frame, text="Run Dry Scan", command=self.run_scan).pack(
            side=tk.LEFT, padx=5
        )
        self.move_btn = Button(
            action_frame,
            text="Move Unused EODs",
            command=self.move_files,
            state=tk.DISABLED,
        )
        self.move_btn.pack(side=tk.LEFT, padx=5)

        Checkbutton(
            action_frame, text="Use Threading", variable=self.use_threading
        ).pack(side=tk.RIGHT, padx=5)

        # Log Level Selection
        Label(action_frame, text="Log Level:").pack(side=tk.LEFT, padx=5)
        self.log_level = Combobox(
            action_frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
        )
        self.log_level.current(1)
        self.log_level.pack(side=tk.LEFT, padx=5)
        self.log_level.bind("<<ComboboxSelected>>", self.set_log_level)

        # Progress Bar
        self.progress = Progressbar(
            main_frame, orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(pady=10, fill=tk.X)

        # Treeview
        self.tree = Treeview(
            main_frame,
            columns=(
                "File Path",
                "File Name",
                "Creation Date",
                "Status",
                "Runspec File",
            ),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Filter
        self.filter_var = tk.StringVar(value="All")
        self.filter_menu = Combobox(
            main_frame,
            textvariable=self.filter_var,
            values=["All", "Used", "Unused"],
            state="readonly",
        )
        self.filter_menu.pack(pady=5)
        self.filter_menu.bind("<<ComboboxSelected>>", self.filter_tree)

        # Log Output
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

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
            self.move_btn.config(state=tk.NORMAL)

    def run_scan(self):
        if not self.cleaner.root_folder:
            messagebox.showerror("Error", "Select a root folder first!")
            return
        self.progress.start()
        if self.use_threading.get():
            threading.Thread(target=self._run_scan, daemon=True).start()
        else:
            self._run_scan()

    def _run_scan(self):
        runspec_files = self.cleaner.find_runspec_files()
        self.cleaner.extract_runspec_metadata(runspec_files)
        unused_eods = self.cleaner.list_unused_eods()
        self.progress.stop()
        if not unused_eods:
            self.logger.info("No EOD files found.")
            messagebox.showinfo("Info", "No EOD files found.")
            return
        self.cleaner.save_metadata(unused_eods)
        self.logger.info("Scan completed and metadata saved.")
        messagebox.showinfo("Success", "Scan completed and metadata saved.")
        self.display_results(unused_eods)

    def display_results(self, eods):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for eod in eods:
            creation_date = datetime.strptime(eod[2], "%Y-%m-%d %H:%M:%S").strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.tree.insert(
                "", "end", values=(eod[0], eod[1], creation_date, eod[3], eod[4])
            )

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
            "Confirm Move", "Move unused EODs? This action is irreversible."
        ):
            self.progress.start()
            if self.use_threading.get():
                threading.Thread(target=self._move_files, daemon=True).start()
            else:
                self._move_files()

    def _move_files(self):
        self.cleaner.move_eods()
        self.progress.stop()
        self.logger.info("Unused EODs moved.")
        messagebox.showinfo("Success", "Unused EODs moved.")


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.after(0, lambda: self.text_widget.insert(tk.END, msg + "\n"))
