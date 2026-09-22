#!/usr/bin/env python3

"""
Recursively QC all mzXML files inside the organised directory.

Checks:
1. Can the mzXML file be parsed?
2. Does the file contain spectra?
3. Do the spectra contain spectral peaks?

Outputs:
- corrupt_files_log.csv
- warnings_log.csv
- qc_master_log.csv

Author: G. Oyedele
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import csv
from datetime import datetime

from pyteomics import mzxml


# ============================================================
# PATHS
# ============================================================

# Main folder containing all organised folders/subfolders
SEARCH_FOLDER = "/Users/g.oyedele/Documents/mzxml/organised"

# Metadata/logging directory
METADATA_FOLDER = "/Users/g.oyedele/Documents/mzxml/metadata_spec_check"

# Individual log files
CORRUPT_LOG_PATH = os.path.join(
    "/Users/g.oyedele/Documents/mzxml/metadata_spec_check",
    "corrupt_files_log.csv"
)

WARNINGS_LOG_PATH = os.path.join(
    METADATA_FOLDER,
    "warnings_log.csv"
)

MASTER_LOG_PATH = os.path.join(
    METADATA_FOLDER,
    "qc_master_log.csv"
)


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

os.makedirs(METADATA_FOLDER, exist_ok=True)


# ============================================================
# GENERAL CSV LOGGING FUNCTION
# ============================================================

def write_log(log_path, log_entry, fieldnames):
    """
    Append one entry to a CSV log.

    If the CSV does not already exist, create it and write
    the column headers first.
    """

    file_exists = os.path.isfile(log_path)

    with open(
        log_path,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as log_file:

        writer = csv.DictWriter(
            log_file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(log_entry)


# ============================================================
# WARNING LOG
# ============================================================

def warnings_log(
    file_path,
    relative_path,
    filename,
    issue_type,
    detail
):
    """
    Record warnings in warnings_log.csv.
    """

    write_log(
        WARNINGS_LOG_PATH,
        {
            "timestamp":
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "file_path":
                file_path,

            "relative_path":
                relative_path,

            "filename":
                filename,

            "issue_type":
                issue_type,

            "detail":
                detail,
        },
        fieldnames=[
            "timestamp",
            "file_path",
            "relative_path",
            "filename",
            "issue_type",
            "detail",
        ],
    )


# ============================================================
# MASTER QC LOG
# ============================================================

def master_log(
    issue_type,
    file_path,
    relative_path,
    filename,
    detail
):
    """
    Record all QC problems in qc_master_log.csv.
    """

    write_log(
        MASTER_LOG_PATH,
        {
            "timestamp":
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "issue_type":
                issue_type,

            "file_path":
                file_path,

            "relative_path":
                relative_path,

            "filename":
                filename,

            "detail":
                detail,
        },
        fieldnames=[
            "timestamp",
            "issue_type",
            "file_path",
            "relative_path",
            "filename",
            "detail",
        ],
    )


# ============================================================
# EMPTY SPECTRUM LOGGING
# ============================================================

def log_empty_spectrum(
    file_path,
    relative_path,
    filename,
    spectrum_count,
    total_peaks
):
    """
    Log an mzXML file that parsed successfully but contained
    no usable spectral data.
    """

    if spectrum_count == 0:

        detail = (
            f"'{filename}' parsed successfully but contained "
            f"zero spectra."
        )

        issue_type = "no_spectra"

    else:

        detail = (
            f"'{filename}' contained {spectrum_count} spectra "
            f"but zero spectral peaks."
        )

        issue_type = "empty_spectrum"

    # Warning log
    warnings_log(
        file_path=file_path,
        relative_path=relative_path,
        filename=filename,
        issue_type=issue_type,
        detail=detail,
    )

    # Master QC log
    master_log(
        issue_type=f"WARNING:{issue_type}",
        file_path=file_path,
        relative_path=relative_path,
        filename=filename,
        detail=detail,
    )


# ============================================================
# CORRUPT FILE LOGGING
# ============================================================

def log_corrupt(
    file_path,
    relative_path,
    filename,
    error
):
    """
    Log an mzXML file that cannot be parsed.
    """

    error_text = str(error)

    detail = (
        f"Unable to parse '{filename}'. "
        f"Parser error: {error_text}"
    )

    # --------------------------------------------------------
    # Dedicated corrupt file log
    # --------------------------------------------------------

    write_log(
        CORRUPT_LOG_PATH,
        {
            "timestamp":
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "file_path":
                file_path,

            "relative_path":
                relative_path,

            "filename":
                filename,

            "error":
                error_text,
        },
        fieldnames=[
            "timestamp",
            "file_path",
            "relative_path",
            "filename",
            "error",
        ],
    )

    # --------------------------------------------------------
    # Warning log
    # --------------------------------------------------------

    warnings_log(
        file_path=file_path,
        relative_path=relative_path,
        filename=filename,
        issue_type="corrupt_file",
        detail=detail,
    )

    # --------------------------------------------------------
    # Master QC log
    # --------------------------------------------------------

    master_log(
        issue_type="CORRUPT",
        file_path=file_path,
        relative_path=relative_path,
        filename=filename,
        detail=detail,
    )


# ============================================================
# CHECK ONE mzXML FILE
# ============================================================

def check_mzxml_file(file_path):
    """
    Parse and QC one mzXML file.

    Returns a dictionary containing:

        status
        spectrum_count
        total_peaks

    Possible status values:

        ok
        no_spectra
        empty_spectrum
        corrupt
    """

    filename = os.path.basename(file_path)

    relative_path = os.path.relpath(
        file_path,
        SEARCH_FOLDER
    )

    spectrum_count = 0
    total_peaks = 0

    try:

        # ----------------------------------------------------
        # Open mzXML file
        # ----------------------------------------------------

        with mzxml.MzXML(file_path) as reader:

            # ------------------------------------------------
            # Read every spectrum
            # ------------------------------------------------

            for spectrum in reader:

                spectrum_count += 1

                # --------------------------------------------
                # Get m/z values
                # --------------------------------------------

                mz_array = spectrum.get(
                    "m/z array"
                )

                # --------------------------------------------
                # Count spectral peaks
                # --------------------------------------------

                if mz_array is not None:
                    total_peaks += len(mz_array)

        # ====================================================
        # FILE CONTAINS NO SPECTRA
        # ====================================================

        if spectrum_count == 0:

            log_empty_spectrum(
                file_path=file_path,
                relative_path=relative_path,
                filename=filename,
                spectrum_count=spectrum_count,
                total_peaks=total_peaks,
            )

            return {
                "status": "no_spectra",
                "spectrum_count": spectrum_count,
                "total_peaks": total_peaks,
            }

        # ====================================================
        # SPECTRA EXIST BUT NO PEAKS
        # ====================================================

        if total_peaks == 0:

            log_empty_spectrum(
                file_path=file_path,
                relative_path=relative_path,
                filename=filename,
                spectrum_count=spectrum_count,
                total_peaks=total_peaks,
            )

            return {
                "status": "empty_spectrum",
                "spectrum_count": spectrum_count,
                "total_peaks": total_peaks,
            }

        # ====================================================
        # FILE IS OK
        # ====================================================

        return {
            "status": "ok",
            "spectrum_count": spectrum_count,
            "total_peaks": total_peaks,
        }

    # ========================================================
    # PARSING FAILED
    # ========================================================

    except Exception as error:

        log_corrupt(
            file_path=file_path,
            relative_path=relative_path,
            filename=filename,
            error=error,
        )

        return {
            "status": "corrupt",
            "spectrum_count": spectrum_count,
            "total_peaks": total_peaks,
        }


# ============================================================
# RECURSIVELY SCAN ORGANISED DIRECTORY
# ============================================================

def scan_organised_folder(search_folder):
    """
    Recursively scan every directory and subdirectory inside
    the organised folder and QC every mzXML file.
    """

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    total_files = 0
    ok_files = 0
    no_spectra_files = 0
    empty_spectrum_files = 0
    corrupt_files = 0

    folders_checked = 0

    # --------------------------------------------------------
    # Start message
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("mzXML QC SCAN")
    print("=" * 70)

    print(f"Search folder:")
    print(f"  {search_folder}")

    print()
    print("Scanning directories...")
    print()

    # ========================================================
    # WALK THROUGH EVERY DIRECTORY
    # ========================================================

    for root, dirs, files in os.walk(search_folder):

        folders_checked += 1

        print("-" * 70)
        print(f"Folder {folders_checked}:")
        print(root)

        # ----------------------------------------------------
        # Find mzXML files in this directory
        # ----------------------------------------------------

        mzxml_files = [
            filename
            for filename in files
            if filename.lower().endswith(".mzxml")
        ]

        # ----------------------------------------------------
        # Report folders containing no mzXML files
        # ----------------------------------------------------

        if not mzxml_files:

            print("  No mzXML files found.")

            continue

        print(
            f"  Found {len(mzxml_files)} mzXML file(s)"
        )

        # ====================================================
        # CHECK EACH mzXML FILE
        # ====================================================

        for filename in sorted(mzxml_files):

            total_files += 1

            file_path = os.path.join(
                root,
                filename
            )

            print()
            print(
                f"  [{total_files}] Checking:"
            )

            print(
                f"      {filename}"
            )

            # ------------------------------------------------
            # Run QC
            # ------------------------------------------------

            result = check_mzxml_file(
                file_path
            )

            status = result["status"]

            spectrum_count = result[
                "spectrum_count"
            ]

            total_peaks = result[
                "total_peaks"
            ]

            # =================================================
            # REPORT RESULT
            # =================================================

            if status == "ok":

                ok_files += 1

                print(
                    f"      OK"
                )

                print(
                    f"      Spectra: "
                    f"{spectrum_count:,}"
                )

                print(
                    f"      Peaks:   "
                    f"{total_peaks:,}"
                )

            elif status == "no_spectra":

                no_spectra_files += 1

                print(
                    "      WARNING: "
                    "No spectra found"
                )

            elif status == "empty_spectrum":

                empty_spectrum_files += 1

                print(
                    "      WARNING: "
                    "Spectra found but no peaks"
                )

                print(
                    f"      Spectra: "
                    f"{spectrum_count:,}"
                )

            elif status == "corrupt":

                corrupt_files += 1

                print(
                    "      CORRUPT: "
                    "Unable to parse file"
                )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("QC SCAN COMPLETE")
    print("=" * 70)

    print(
        f"Folders checked          : "
        f"{folders_checked:,}"
    )

    print(
        f"Total mzXML files        : "
        f"{total_files:,}"
    )

    print(
        f"OK files                 : "
        f"{ok_files:,}"
    )

    print(
        f"No spectra                : "
        f"{no_spectra_files:,}"
    )

    print(
        f"Spectra but zero peaks    : "
        f"{empty_spectrum_files:,}"
    )

    print(
        f"Corrupt files             : "
        f"{corrupt_files:,}"
    )

    problem_files = (
        no_spectra_files
        + empty_spectrum_files
        + corrupt_files
    )

    print(
        f"Total files with problems : "
        f"{problem_files:,}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Log locations
    # --------------------------------------------------------

    print()
    print("LOG FILES")
    print("-" * 70)

    print(
        f"Corrupt files:"
    )
    print(
        f"  {CORRUPT_LOG_PATH}"
    )

    print()

    print(
        f"Warnings:"
    )
    print(
        f"  {WARNINGS_LOG_PATH}"
    )

    print()

    print(
        f"Master QC log:"
    )
    print(
        f"  {MASTER_LOG_PATH}"
    )

    print()

    # --------------------------------------------------------
    # Warn if no files were detected at all
    # --------------------------------------------------------

    if total_files == 0:

        print(
            "WARNING: No mzXML files were found."
        )

        print(
            "Check that SEARCH_FOLDER is correct "
            "and that the files have .mzXML extensions."
        )

        print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Verify main directory exists
    # --------------------------------------------------------

    if not os.path.isdir(SEARCH_FOLDER):

        raise FileNotFoundError(
            "\n\nSearch folder does not exist:\n"
            f"{SEARCH_FOLDER}\n\n"
            "Please check the SEARCH_FOLDER path."
        )

    # --------------------------------------------------------
    # Start recursive scan
    # --------------------------------------------------------

    scan_organised_folder(
        SEARCH_FOLDER
    )