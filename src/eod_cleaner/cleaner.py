# eod_cleaner.py - Backend

import shutil
import json
import logging
import pandas as pd
from pathlib import Path


class EODCleaner:
    def __init__(self, log_file="eod_cleanup.log", metadata_file="eod_metadata.xlsx"):
        self.root_folder = None
        self.archive_folder = None
        self.runspec_data = set()
        self.metadata_file = Path(metadata_file)

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def set_folders(self, root_folder, archive_folder):
        self.root_folder = Path(root_folder)
        self.archive_folder = Path(archive_folder)

    def find_runspec_files(self):
        return list(self.root_folder.rglob("*.runspec.json"))

    def extract_runspec_metadata(self, runspec_files):
        for runspec in runspec_files:
            try:
                with runspec.open("r") as file:
                    data = json.load(file)
                    for entry in data:
                        for eod in entry.get("inputs", []):
                            self.runspec_data.add(Path(eod).name)
                        output_eod = entry.get("output")
                        if output_eod:
                            self.runspec_data.add(Path(output_eod).name)
            except Exception as e:
                logging.error(f"Error reading {runspec}: {e}")
        logging.info(f"Extracted metadata for {len(self.runspec_data)} EODs.")

    def list_unused_eods(self):
        unused_eods = []
        for eod in self.root_folder.rglob("*.eod"):
            creation_date = eod.stat().st_ctime
            if eod.name not in self.runspec_data:
                unused_eods.append([str(eod), eod.name, creation_date])
        logging.info(f"Found {len(unused_eods)} unused EOD files.")
        return unused_eods

    def save_metadata(self, unused_eods):
        df = pd.DataFrame(
            unused_eods, columns=["File Path", "File Name", "Creation Date"]
        )
        df.to_excel(self.metadata_file, index=False)
        logging.info(f"Saved metadata to {self.metadata_file}")

    def load_metadata(self):
        if self.metadata_file.exists():
            return pd.read_excel(self.metadata_file)
        return None

    def move_eods(self):
        df = self.load_metadata()
        if df is None:
            logging.error("No metadata found. Run dry scan first.")
            return
        self.archive_folder.mkdir(parents=True, exist_ok=True)

        for _, row in df.iterrows():
            eod_path = Path(row["File Path"])
            if eod_path.exists():
                shutil.move(str(eod_path), str(self.archive_folder / eod_path.name))
                logging.info(f"Moved {eod_path} to archive.")
