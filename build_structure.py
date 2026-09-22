#!/usr/bin/env python3
"""
build_structure.py

Organise mzXML files into isolate folders.

Reads:
    metadata/isolate_inventory.csv

Creates:

organised/

1/
    1_rep1.mzXML
    1_rep2.mzXML
    1_rep3.mzXML

2/
...

1053/

The script NEVER scans the raw data.
"""

from pathlib import Path
import pandas as pd
import shutil
import logging
import sys

###############################################################################
# USER SETTINGS
###############################################################################

INVENTORY = Path("metadata/isolate_inventory.csv")

OUTPUT_DIRECTORY = Path("organised")

OUTPUT_DIRECTORY.mkdir(exist_ok=True)

EXPECTED_ISOLATES = 1053

# copy OR symlink
COPY_MODE = "copy"

# overwrite existing files?
OVERWRITE = False

###############################################################################
# LOGGING
###############################################################################

logging.basicConfig(
    filename="build_structure.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

###############################################################################
# CHECK INVENTORY
###############################################################################

if not INVENTORY.exists():

    print()

    print("ERROR")

    print("Inventory not found.")

    print(INVENTORY)

    print()

    sys.exit(1)

inventory = pd.read_csv(INVENTORY)

###############################################################################
# QC WARNING
###############################################################################

duplicates = (

    inventory

    .groupby(["isolate","replicate"])

    .size()

    .reset_index(name="count")

)

duplicates = duplicates[duplicates["count"]>1]

if len(duplicates):

    print()

    print("WARNING")

    print(f"{len(duplicates)} duplicate replicate(s) detected.")

    print()

###############################################################################
# CREATE ALL ISOLATE FOLDERS
###############################################################################

print("Creating isolate folders...")

for isolate in range(1, EXPECTED_ISOLATES + 1):

    (OUTPUT_DIRECTORY / str(isolate)).mkdir(

        exist_ok=True

    )

###############################################################################
# COPY FILES
###############################################################################

copied = 0

skipped = 0

failed = 0

manifest = []

print("Copying mzXML files...")

for _, row in inventory.iterrows():

    source = Path(row["full_path"])

    destination = (

        OUTPUT_DIRECTORY

        / str(row["isolate"])

        / row["file_name"]

    )

    manifest.append({

        "isolate": row["isolate"],

        "replicate": row["replicate"],

        "source": str(source),

        "destination": str(destination)

    })

    if not source.exists():

        logging.warning(f"Missing source: {source}")

        failed += 1

        continue

    if destination.exists():

        if OVERWRITE:

            destination.unlink()

        else:

            skipped += 1

            continue

    try:

        if COPY_MODE.lower() == "copy":

            shutil.copy2(

                source,

                destination

            )

        elif COPY_MODE.lower() == "symlink":

            destination.symlink_to(source)

        else:

            raise ValueError(

                "COPY_MODE must be copy or symlink"

            )

        copied += 1

        logging.info(f"Copied {source}")

    except Exception as e:

        failed += 1

        logging.error(f"{source}: {e}")

###############################################################################
# MANIFEST
###############################################################################

manifest = pd.DataFrame(manifest)

manifest.to_csv(

    OUTPUT_DIRECTORY/"manifest.csv",

    index=False

)

###############################################################################
# SUMMARY
###############################################################################

print()

print("="*70)

print("BUILD COMPLETE")

print("="*70)

print()

print(f"Folders created              : {EXPECTED_ISOLATES}")

print(f"Files copied                 : {copied}")

print(f"Files skipped                : {skipped}")

print(f"Copy failures                : {failed}")

print()

print("Manifest written to")

print(OUTPUT_DIRECTORY/"manifest.csv")

print()

logging.info("="*60)

logging.info("BUILD COMPLETE")

logging.info(f"Files copied : {copied}")

logging.info(f"Skipped : {skipped}")

logging.info(f"Failed : {failed}")

logging.info("="*60)