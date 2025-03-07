import shutil
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime


class EODCleaner:
    def __init__(self, log_file="eod_cleanup.log", metadata_file=None):
        self.root_folder = None
        self.archive_folder = None
        self.runspec_data = {}
        self.metadata_file = (
            Path(metadata_file)
            if metadata_file
            else Path.home() / "Downloads" / "eod_metadata.xlsx"
        )

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
                            self.runspec_data[Path(eod).name] = str(runspec)
                        output_eod = entry.get("output")
                        if output_eod:
                            self.runspec_data[Path(output_eod).name] = str(runspec)
            except Exception as e:
                logging.error(f"Error reading {runspec}: {e}")
        logging.info(f"Extracted metadata for {len(self.runspec_data)} EODs.")

    def list_unused_eods(self):
        unused_eods = []
        used_count = 0
        unused_count = 0
        for eod in self.root_folder.rglob("*.eod"):
            creation_date = eod.stat().st_ctime
            status = "Unused"
            runspec_file = ""
            if eod.name in self.runspec_data:
                status = "Used"
                runspec_file = self.runspec_data[eod.name]
                used_count += 1
            else:
                unused_count += 1
            unused_eods.append(
                [str(eod), eod.name, creation_date, status, runspec_file]
            )
        logging.info(
            f"Found {len(unused_eods)} EOD files: {used_count} used, {unused_count} unused."
        )
        return unused_eods

    def save_metadata(self, eods):
        # Convert Unix timestamp to human-readable date format
        for eod in eods:
            eod[2] = datetime.fromtimestamp(eod[2]).strftime("%Y-%m-%d %H:%M:%S")

        df = pd.DataFrame(
            eods,
            columns=[
                "File Path",
                "File Name",
                "Creation Date",
                "Status",
                "Runspec File",
            ],
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
            if eod_path.exists() and row["Status"] == "Unused":
                shutil.move(str(eod_path), str(self.archive_folder / eod_path.name))
                logging.info(f"Moved {eod_path} to archive.")
