#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import shutil
import logging
import re

###############################################################################
# USER SETTINGS
###############################################################################

EXTRA_FOLDER = Path("EXTRA_REPLICATE")

ORGANISED_FOLDER = Path("organised")

MAPPING_FILE = Path("code_ID.xlsx")

CODE_COLUMN = "code"

STRAIN_COLUMN = "StrainID"

OVERWRITE = False

###############################################################################
# LOGGING
###############################################################################

logging.basicConfig(

    filename="import_extra_replicates.log",

    level=logging.INFO,

    format="%(asctime)s %(levelname)s %(message)s"

)

###############################################################################
# LOAD MAPPING
###############################################################################

mapping = pd.read_excel(MAPPING_FILE)

mapping[CODE_COLUMN] = mapping[CODE_COLUMN].astype(str)

lookup = dict(

    zip(

        mapping[CODE_COLUMN],

        mapping[STRAIN_COLUMN]

    )

)

###############################################################################
# REGEX
###############################################################################

pattern = re.compile(

    r"^(\d+)_rep(\d+)\.mzXML$",

    re.IGNORECASE

)

###############################################################################
# COUNTERS
###############################################################################

moved = 0

skipped = 0

missing_mapping = []

invalid_names = []

manifest = []

###############################################################################
# LOOP THROUGH EXTRA FILES
###############################################################################

for file in EXTRA_FOLDER.glob("*.mzXML"):

    match = pattern.match(file.name)

    if not match:

        invalid_names.append(file.name)

        continue

    code = match.group(1)

    replicate = match.group(2)

    ##########################################################

    if code not in lookup:

        missing_mapping.append(code)

        continue

    ##########################################################

    strain = str(lookup[code])

    destination_folder = ORGANISED_FOLDER / strain

    destination_folder.mkdir(exist_ok=True)

    destination = (

        destination_folder /

        f"{strain}_rep{replicate}.mzXML"

    )

    ##########################################################

    if destination.exists():

        if OVERWRITE:

            destination.unlink()

        else:

            skipped += 1

            continue

    ##########################################################

    shutil.move(

        str(file),

        str(destination)

    )

    moved += 1

    manifest.append({

        "Code": code,

        "StrainID": strain,

        "Replicate": replicate,

        "Destination": str(destination)

    })

###############################################################################
# SAVE MANIFEST
###############################################################################

pd.DataFrame(manifest).to_csv(

    "extra_replicates_manifest.csv",

    index=False

)

###############################################################################
# SUMMARY
###############################################################################

print()

print("="*70)

print("EXTRA REPLICATE IMPORT COMPLETE")

print("="*70)

print()

print(f"Files moved          : {moved}")

print(f"Skipped              : {skipped}")

print(f"Missing mapping      : {len(set(missing_mapping))}")

print(f"Invalid filenames    : {len(invalid_names)}")

print()

if invalid_names:

    print("Invalid filenames:")

    for f in invalid_names:

        print("  ", f)

    print()

if missing_mapping:

    print("Codes missing from mapping:")

    print(", ".join(sorted(set(missing_mapping), key=int)))

print()

print("Manifest written to")

print("extra_replicates_manifest.csv")

logging.info(f"Moved: {moved}")

logging.info(f"Skipped: {skipped}")