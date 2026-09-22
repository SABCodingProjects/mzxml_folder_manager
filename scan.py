#!/usr/bin/env python3
"""
scan.py

Scan mzXML sequencing files and create an inventory.

Expected directory structure
----------------------------

RAW_DIRECTORY/
│
├── 12Feb26 170-208/
│   ├── rep1/
│   │   ├── 170_rep1.mzXML
│   │   ├── 171_rep1.mzXML
│   │   └── ...
│   ├── rep2/
│   └── rep3/
│
├── 18Dec25 14-26/
│   ├── rep1/
│   ├── rep2/
│   └── rep3/
│
└── ...

Outputs
-------
metadata/
    isolate_inventory.csv
    scan.log
"""

from pathlib import Path
import pandas as pd
import logging
import re
import sys

###############################################################################
# USER SETTINGS
###############################################################################

RAW_DIRECTORY = Path("/Users/g.oyedele/Documents/mzxml")

OUTPUT_DIRECTORY = Path("metadata")
OUTPUT_DIRECTORY.mkdir(exist_ok=True)

###############################################################################
# LOGGING
###############################################################################

logging.basicConfig(
    filename=OUTPUT_DIRECTORY / "scan.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

###############################################################################
# FILE NAME PATTERN
###############################################################################

# Matches:
# 170_rep1.mzXML
# 501_rep2.mzXML
# 1053_rep3.mzXML

FILE_PATTERN = re.compile(
    r"^(\d+)_rep([123])\.mzXML$",
    re.IGNORECASE
)

###############################################################################
# START
###############################################################################

print("=" * 70)
print("Scanning mzXML files...")
print("=" * 70)

print(f"Raw directory : {RAW_DIRECTORY.resolve()}")
print(f"Exists        : {RAW_DIRECTORY.exists()}")
print()

if not RAW_DIRECTORY.exists():
    print("ERROR: Raw directory does not exist.")
    sys.exit(1)

records = []

###############################################################################
# SCAN
###############################################################################

for file in RAW_DIRECTORY.rglob("*.mzXML"):

    match = FILE_PATTERN.match(file.name)

    if not match:
        logging.warning(f"Invalid filename: {file}")
        continue

    isolate = match.group(1)

    replicate = f"rep{match.group(2)}"

    replicate_folder = file.parent.name

    hierarchy_ok = replicate_folder == replicate

    try:
        batch = file.parent.parent.name
    except IndexError:
        batch = ""

    records.append({

        "batch" : batch,

        "isolate" : isolate,

        "replicate" : replicate,

        "file_name" : file.name,

        "replicate_folder" : replicate_folder,

        "hierarchy_ok" : hierarchy_ok,

        "file_size_MB" : round(file.stat().st_size / (1024*1024),2),

        "full_path" : str(file.resolve())

    })

###############################################################################
# BUILD INVENTORY
###############################################################################

inventory = pd.DataFrame(
    records,
    columns=[
        "batch",
        "isolate",
        "replicate",
        "file_name",
        "replicate_folder",
        "hierarchy_ok",
        "file_size_MB",
        "full_path"
    ]
)

if inventory.empty:

    print("No mzXML files matched the expected naming convention.")
    print("Expected example:")
    print("    176_rep1.mzXML")

    sys.exit()

###############################################################################
# SORT
###############################################################################

inventory["isolate_numeric"] = inventory["isolate"].astype(int)

inventory = inventory.sort_values(
    ["isolate_numeric","replicate"]
)

inventory.drop(columns="isolate_numeric", inplace=True)

###############################################################################
# SAVE
###############################################################################

inventory.to_csv(

    OUTPUT_DIRECTORY / "isolate_inventory.csv",

    index=False

)


###############################################################################
# EXPECTED ISOLATES
###############################################################################

EXPECTED_ISOLATES = {str(i) for i in range(1, 1054)}

FOUND_ISOLATES = set(inventory["isolate"])

MISSING_ISOLATES = sorted(
    EXPECTED_ISOLATES - FOUND_ISOLATES,
    key=int
)


###############################################################################
# MISSING REPLICATES
###############################################################################

missing_replicates = []

for isolate in sorted(FOUND_ISOLATES, key=int):

    subset = inventory[inventory["isolate"] == isolate]

    found = set(subset["replicate"])

    for rep in ["rep1", "rep2", "rep3"]:

        if rep not in found:

            missing_replicates.append({

                "isolate": isolate,

                "missing_replicate": rep

            })

missing_replicates_df = pd.DataFrame(missing_replicates)

missing_replicates_df.to_csv(

    OUTPUT_DIRECTORY / "missing_replicates.csv",

    index=False

)


###############################################################################
# DUPLICATE REPLICATES
###############################################################################

duplicates = (

    inventory

    .groupby(["isolate", "replicate"])

    .size()

    .reset_index(name="count")

)

duplicates = duplicates[duplicates["count"] > 1]

duplicates.to_csv(

    OUTPUT_DIRECTORY / "duplicate_replicates.csv",

    index=False

)


###############################################################################
# MISSING ISOLATES
###############################################################################

missing_isolates_df = pd.DataFrame({

    "missing_isolate": MISSING_ISOLATES

})

missing_isolates_df.to_csv(

    OUTPUT_DIRECTORY / "missing_isolates.csv",

    index=False

)


###############################################################################
# HIERARCHY PROBLEMS
###############################################################################

hierarchy_errors = inventory[~inventory["hierarchy_ok"]]

hierarchy_errors.to_csv(

    OUTPUT_DIRECTORY / "hierarchy_errors.csv",

    index=False

)






###############################################################################
# SUMMARY
###############################################################################

print()
print("=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

print(f"Total mzXML files scanned        : {len(inventory)}")

print(f"Unique isolates found            : {inventory['isolate'].nunique()}")

print()

print(f"rep1 files                       : {(inventory['replicate']=='rep1').sum()}")

print(f"rep2 files                       : {(inventory['replicate']=='rep2').sum()}")

print(f"rep3 files                       : {(inventory['replicate']=='rep3').sum()}")

print()

print(f"Completely missing isolates      : {len(MISSING_ISOLATES)}")

print(f"Missing replicate files          : {len(missing_replicates_df)}")

print(f"Duplicate replicate files        : {len(duplicates)}")

print(f"Hierarchy problems               : {len(hierarchy_errors)}")

print("Reports written to:")

print(OUTPUT_DIRECTORY)

print()

if len(MISSING_ISOLATES):

    print("Missing isolates:")

    print(", ".join(MISSING_ISOLATES))

    print()

if len(missing_replicates_df):

    print("First 20 missing replicates:")

    print(missing_replicates_df.head(20).to_string(index=False))

    print()

if len(duplicates):

    print("Duplicate replicate files detected.")

    print()

if len(hierarchy_errors):

    print("Hierarchy problems detected.")

    print()

    
###############################################################################
# LOG FILE
###############################################################################

logging.info("=" * 60)
logging.info("SCAN COMPLETE")
logging.info(f"Total files: {len(inventory)}")
logging.info(f"Unique isolates: {inventory['isolate'].nunique()}")
logging.info(f"Missing isolates: {len(MISSING_ISOLATES)}")
logging.info(f"Missing replicates: {len(missing_replicates_df)}")
logging.info(f"Duplicate replicates: {len(duplicates)}")
logging.info(f"Hierarchy problems: {len(hierarchy_errors)}")
logging.info("=" * 60)