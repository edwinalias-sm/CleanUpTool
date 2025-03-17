import shutil
import json
import logging
import pandas as pd
import platform
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        """Set root and archive folders (supports network drives)."""
        self.root_folder = self._resolve_path(root_folder)
        self.archive_folder = self._resolve_path(archive_folder)

    def _resolve_path(self, path):
        """Resolve UNC paths on Windows and absolute paths on Linux."""
        path = Path(path)
        if platform.system() == "Windows":
            return Path(path).resolve()
        return path.absolute()

    def find_runspec_files(self):
        """Find all .runspec.json files in the root folder."""
        return list(self.root_folder.rglob("*.runspec.json"))

    def _resolve_runspec_path(self, input_file, actual_file_path):
        """Resolve EOD paths from the 'inputs' list in the runspec file."""
        # Convert Path to string if needed
        actual_file_path = (
            Path(actual_file_path)
            if not isinstance(actual_file_path, Path)
            else actual_file_path
        )
        if input_file.endswith(".eod"):
            # Trans linux path to P drive path for Windows
            if platform.system() == "Windows" and "/mnt/public/" in input_file:
                input_file = input_file.replace("/mnt/public/", "P:/")

            # For checking EOD in "recordings" test case folder
            if not "FLIB" in input_file:
                # Replace /v1/query to the end by input_file
                fix_str_path = actual_file_path.as_posix()
                input_file = re.sub(r"v1/query.*$", input_file, fix_str_path)

        return Path(input_file)

    def extract_runspec_metadata(self, runspec_files):
        """Extract metadata from .runspec.json files."""
        for runspec in runspec_files:
            try:
                with runspec.open("r") as file:
                    data = json.load(file)
                    for entry in data:
                        for eod in entry.get("inputs", []):
                            self.runspec_data[Path(eod).name] = {
                                "Runspecfile": str(runspec),
                                "actual_eod_path": self._resolve_runspec_path(
                                    eod, runspec
                                ),
                            }
                        # output_eod = entry.get("output")
                        # if output_eod:
                        # self.runspec_data[Path(output_eod).name] = str(runspec)
                logging.debug(f"Extracted metadata form file: {runspec} ")
            except Exception as e:
                logging.error(f"Error reading {runspec}: {e}")

    def list_unused_eods(self):
        """List unused EOD files based on metadata."""
        unused_eods = []
        used_count = 0
        unused_count = 0
        missing_count = 0
        # Track found EODs
        found_eods = set()

        for eod in self.root_folder.rglob("*.eod"):
            creation_date = eod.stat().st_ctime
            status = "Unused"
            runspec_file = ""
            input_runspec_path = ""
            if eod.name in self.runspec_data:
                status = "Used"
                runspec_file = self.runspec_data[eod.name]["Runspecfile"]
                input_runspec_path = self.runspec_data[eod.name]["actual_eod_path"]
                used_count += 1
                found_eods.add(eod.name)
            else:
                unused_count += 1
            unused_eods.append(
                [
                    str(eod),
                    eod.name,
                    creation_date,
                    status,
                    runspec_file,
                    input_runspec_path,
                ]
            )
            # Check for missing EODs in runspec_data
        for eod_name, eod_info in self.runspec_data.items():
            if eod_name not in found_eods:
                missing_count += 1
                unused_eods.append(
                    [
                        "",
                        eod_name,
                        None,
                        "Missing",
                        eod_info["Runspecfile"],
                        eod_info["actual_eod_path"],
                    ]
                )
        logging.info(
            f"Found {len(unused_eods)} EOD files: {used_count} used, {unused_count} unused."
        )
        return unused_eods

    def save_metadata(self, eods):
        """Save EOD metadata to an Excel file."""
        for eod in eods:
            if eod[2] is not None:  # Ensure creation date is valid
                if isinstance(eod[2], (int, float)):
                    eod[2] = datetime.fromtimestamp(eod[2]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            else:
                eod[2] = "N/A"  # Assign a default value for missing files
        df = pd.DataFrame(
            eods,
            columns=[
                "File Path",
                "File Name",
                "Creation Date",
                "Status",
                "Runspec File",
                "Actual Path from runspec",
            ],
        )
        df.to_excel(self.metadata_file, index=False)
        logging.info(f"Saved metadata to {self.metadata_file}")

    def load_metadata(self):
        """Load metadata from an existing Excel file."""
        if self.metadata_file.exists():
            return pd.read_excel(self.metadata_file)
        return None

    def move_eod(self, eod_path):
        """Move a single EOD file to the archive."""
        try:
            shutil.move(str(eod_path), str(self.archive_folder / eod_path.name))
            logging.info(f"Moved {eod_path} to archive.")
        except Exception as e:
            logging.error(f"Error moving {eod_path}: {e}")

    def move_eods(self, use_threading=None):
        """Move all unused EOD files, with optional threading."""
        df = self.load_metadata()
        if df is None:
            logging.error("No metadata found. Run dry scan first.")
            return

        self.archive_folder.mkdir(parents=True, exist_ok=True)

        # Collect file paths
        file_paths = [
            Path(row["File Path"])
            for _, row in df.iterrows()
            if row["Status"] == "Unused"
        ]
        total_files = len(file_paths)

        # Determine execution mode if not explicitly set
        if use_threading is None:
            average_size = (
                sum(f.stat().st_size for f in file_paths if f.exists()) / total_files
                if total_files > 0
                else 0
            )
            use_threading = (
                total_files > 100 or average_size < 50 * 1024 * 1024
            )  # 50MB threshold

        # Execute with or without threading
        if use_threading:
            logging.info(f"Using threading to move {total_files} files.")
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.move_eod, f) for f in file_paths if f.exists()
                ]
                for i, future in enumerate(as_completed(futures)):
                    future.result()
                    logging.info(f"Moved {i + 1}/{total_files} files.")
        else:
            logging.info(f"Using sequential execution to move {total_files} files.")
            for i, file_path in enumerate(file_paths):
                if file_path.exists():
                    self.move_eod(file_path)
                    logging.info(f"Moved {i + 1}/{total_files} files.")
