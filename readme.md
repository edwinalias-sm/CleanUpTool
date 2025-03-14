# EOD Cleaner

EOD Cleaner is a tool designed to build and run test cases from the command line. It helps in managing and cleaning up EOD (End of Day) files by scanning, listing unused files, and moving them to an archive folder.

## Requirements

- Python 3.9 or higher
- pandas
- openpyxl
- tkinter

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/edwinalias-sm/ConsoleTestRunner-main.git
    ```

2. Navigate to the project directory:

    ```sh
    cd eod_cleaner
    ```

3. Install the package in editable mode:

    ```sh
    pip install -e .
    ```

## Usage

1. Run the GUI application:

    ```sh
    python main_gui.py
    ```

2. Use the GUI to select the root folder and archive folder.
3. Click "Run Dry Scan" to scan for unused EOD files.
4. Click "Move Unused EODs" to move the unused and missing EOD files to the archive folder.

## Author

Edwin Alias - [edwin.alias@seeingmachines.com](mailto:edwin.alias@seeingmachines.com)