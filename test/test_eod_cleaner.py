import pytest
import shutil
import json
import pandas as pd
from pathlib import Path
from eod_cleaner.cleaner import EODCleaner


@pytest.fixture
def setup_eod_cleaner(tmp_path):
    """Fixture to initialize EODCleaner with test directories."""
    root_folder = tmp_path / "root"
    archive_folder = tmp_path / "archive"
    root_folder.mkdir()
    archive_folder.mkdir()

    cleaner = EODCleaner(metadata_file=tmp_path / "eod_metadata.xlsx")
    cleaner.set_folders(root_folder, archive_folder)
    return cleaner, root_folder, archive_folder


def test_set_folders(setup_eod_cleaner):
    """Test setting root and archive folders."""
    cleaner, root_folder, archive_folder = setup_eod_cleaner
    assert cleaner.root_folder == root_folder
    assert cleaner.archive_folder == archive_folder


def test_find_runspec_files(setup_eod_cleaner):
    """Test finding .runspec.json files in the root directory."""
    cleaner, root_folder, _ = setup_eod_cleaner
    runspec_file = root_folder / "test.runspec.json"
    runspec_file.write_text(json.dumps([{"inputs": ["file.eod"]}]))

    found_files = cleaner.find_runspec_files()
    assert len(found_files) == 1
    assert found_files[0] == runspec_file


def test_extract_runspec_metadata(setup_eod_cleaner):
    """Test extracting metadata from runspec files."""
    cleaner, root_folder, _ = setup_eod_cleaner
    runspec_file = root_folder / "test.runspec.json"
    runspec_file.write_text(json.dumps([{"inputs": ["/mnt/public/sample.eod"]}]))

    cleaner.extract_runspec_metadata([runspec_file])
    assert "sample.eod" in cleaner.runspec_data
    assert cleaner.runspec_data["sample.eod"]["Runspecfile"] == str(runspec_file)


def test_list_unused_eods(setup_eod_cleaner):
    """Test listing unused EOD files."""
    cleaner, root_folder, _ = setup_eod_cleaner
    eod_file = root_folder / "unused.eod"
    eod_file.touch()

    unused_files = cleaner.list_unused_eods()
    assert any(eod[1] == "unused.eod" and eod[3] == "Unused" for eod in unused_files)


def test_save_metadata(setup_eod_cleaner):
    """Test saving metadata to an Excel file."""
    cleaner, _, _ = setup_eod_cleaner
    test_data = [["path/to/file", "file.eod", "2025-03-17 10:00:00", "Unused", "", ""]]
    cleaner.save_metadata(test_data)

    df = pd.read_excel(cleaner.metadata_file)
    assert df.iloc[0]["File Name"] == "file.eod"


def test_move_eod(setup_eod_cleaner):
    """Test moving an EOD file to the archive folder."""
    cleaner, root_folder, archive_folder = setup_eod_cleaner
    eod_file = root_folder / "test.eod"
    eod_file.touch()

    cleaner.move_eod(eod_file)
    assert not eod_file.exists()
    assert (archive_folder / "test.eod").exists()


def test_move_eods(setup_eod_cleaner):
    """Test moving multiple unused EOD files."""
    cleaner, root_folder, archive_folder = setup_eod_cleaner
    eod_file1 = root_folder / "file1.eod"
    eod_file2 = root_folder / "file2.eod"
    eod_file1.touch()
    eod_file2.touch()

    cleaner.save_metadata(
        [
            [str(eod_file1), "file1.eod", "2025-03-17 10:00:00", "Unused", "", ""],
            [str(eod_file2), "file2.eod", "2025-03-17 10:00:00", "Unused", "", ""],
        ]
    )

    cleaner.move_eods(use_threading=False)
    assert not eod_file1.exists()
    assert not eod_file2.exists()
    assert (archive_folder / "file1.eod").exists()
    assert (archive_folder / "file2.eod").exists()


def test_load_metadata(setup_eod_cleaner):
    """Test loading metadata from an existing Excel file."""
    cleaner, _, _ = setup_eod_cleaner
    test_data = [["path/to/file", "file.eod", "2025-03-17 10:00:00", "Unused", "", ""]]
    cleaner.save_metadata(test_data)

    df = cleaner.load_metadata()
    assert df is not None
    assert df.iloc[0]["File Name"] == "file.eod"


def test_move_eods_with_threading(setup_eod_cleaner):
    """Test moving multiple unused EOD files with threading."""
    cleaner, root_folder, archive_folder = setup_eod_cleaner
    eod_file1 = root_folder / "file1.eod"
    eod_file2 = root_folder / "file2.eod"
    eod_file1.touch()
    eod_file2.touch()

    cleaner.save_metadata(
        [
            [str(eod_file1), "file1.eod", "2025-03-17 10:00:00", "Unused", "", ""],
            [str(eod_file2), "file2.eod", "2025-03-17 10:00:00", "Unused", "", ""],
        ]
    )

    cleaner.move_eods(use_threading=True)
    assert not eod_file1.exists()
    assert not eod_file2.exists()
    assert (archive_folder / "file1.eod").exists()
    assert (archive_folder / "file2.eod").exists()


def test_move_missing_eod(setup_eod_cleaner):
    """Test handling missing EOD file during move."""
    cleaner, root_folder, archive_folder = setup_eod_cleaner
    eod_file = root_folder / "missing.eod"

    cleaner.save_metadata(
        [[str(eod_file), "missing.eod", "2025-03-17 10:00:00", "Unused", "", ""]]
    )

    cleaner.move_eods(use_threading=False)
    assert not (archive_folder / "missing.eod").exists()


def test_find_runspec_files_no_file(setup_eod_cleaner):
    cleaner, _, _ = setup_eod_cleaner
    assert cleaner.find_runspec_files() == []


def test_extract_metadata_invalid_json(setup_eod_cleaner):
    cleaner, source_folder, _ = setup_eod_cleaner
    runspec_file = source_folder / ".runspec.json"
    runspec_file.write_text("INVALID_JSON")
    with pytest.raises(Exception):
        cleaner.extract_metadata(runspec_file)


def test_move_eods_missing_file(setup_eod_cleaner):
    cleaner, source_folder, destination_folder = setup_eod_cleaner
    eod_file = source_folder / "missing.eod"
    cleaner.move_eods(use_threading=False)
    assert not (destination_folder / "missing.eod").exists()


def test_save_metadata_invalid_format(setup_eod_cleaner):
    cleaner, _, _ = setup_eod_cleaner
    cleaner.metadata_file.write_text("INVALID EXCEL CONTENT")  # Corrupt file
    metadata = [{"File Name": "test.eod", "Creation Date": "2023-10-10"}]
    with pytest.raises(Exception):
        cleaner.save_metadata(metadata)


if __name__ == "__main__":
    pytest.main()
