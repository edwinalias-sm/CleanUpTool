import argparse
import logging
import os
from eod_cleaner.cleaner import EODCleaner


def main():
    parser = argparse.ArgumentParser(description="EOD Cleanup Tool")
    parser.add_argument("root_folder", help="Path to the root folder")
    parser.add_argument(
        "archive_folder",
        nargs="?",
        default=None,
        help="Path to the archive folder (default: None)",
    )
    parser.add_argument("--scan", action="store_true", help="Run dry scan")
    parser.add_argument("--move", action="store_true", help="Move unused EODs")

    args = parser.parse_args()

    cleaner = EODCleaner()

    if args.scan:
        cleaner.set_folders(args.root_folder, "")
        logging.info("Running dry scan...")
        runspec_files = cleaner.find_runspec_files()
        cleaner.extract_runspec_metadata(runspec_files)
        unused_eods = cleaner.list_unused_eods()
        cleaner.save_metadata(unused_eods)
        logging.info("Scan completed and metadata saved.")

    if args.move:
        archive_folder = args.archive_folder if args.archive_folder else ""
        cleaner.set_folders(args.root_folder, archive_folder)
        logging.info("Moving unused EODs...")
        cleaner.move_eods()
        logging.info("Unused EODs moved.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
