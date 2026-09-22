#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import logging
import re
import sys

###############################################################################
# USER SETTINGS
###############################################################################

ORGANISED_DIRECTORY = Path("organised")

MAPPING_FILE = Path("code_ID.xlsx")

CODE_COLUMN = "code"

STRAIN_COLUMN = "StrainID"

###############################################################################
# LOGGING
###############################################################################

logging.basicConfig(

    filename="rename_to_strainID.log",

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
# RENAME
###############################################################################

pattern = re.compile(r"^(\d+)_rep([123])\.mzXML$", re.IGNORECASE)

folders_renamed = 0

files_renamed = 0

missing_codes = []

###############################################################################
# RENAME FILES
###############################################################################

for folder in sorted(ORGANISED_DIRECTORY.iterdir()):

    if not folder.is_dir():

        continue

    code = folder.name

    if code not in lookup:

        missing_codes.append(code)

        continue

    strain = str(lookup[code])

    ############################################################

    for file in folder.glob("*.mzXML"):

        m = pattern.match(file.name)

        if not m:

            continue

        rep = m.group(2)

        new_file = folder / f"{strain}_rep{rep}.mzXML"

        file.rename(new_file)

        files_renamed += 1

    ############################################################

    new_folder = folder.parent / strain

    folder.rename(new_folder)

    folders_renamed += 1

###############################################################################
# SUMMARY
###############################################################################

print()

print("="*60)

print("RENAMING COMPLETE")

print("="*60)

print()

print(f"Folders renamed : {folders_renamed}")

print(f"Files renamed   : {files_renamed}")

print()

if len(missing_codes):

    print("Codes missing from mapping")

    print(", ".join(sorted(missing_codes,key=int)))

print()

logging.info(f"Folders renamed: {folders_renamed}")

logging.info(f"Files renamed: {files_renamed}")