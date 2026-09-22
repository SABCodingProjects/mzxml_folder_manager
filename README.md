---
title: "mzXML File Organisation and Quality-Control Workflow"
author: "G. Oyedele"
output: html_document
---

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE, warning = FALSE, message = FALSE)
```

# Overview

This project contains Python scripts for scanning raw mzXML files, checking
their metadata and hierarchy, organising them by isolate, importing additional
replicates, renaming files with StrainID values, counting files, plotting the
file-count distribution, and checking the contents of each mzXML file.

The scripts are command-line Python programs rather than functions in a single
package. Most paths are relative to the directory from which the script is
run, while `scan.py` and `log_Spectral_error.py` contain absolute paths that
should be changed when the project is moved to another computer.

The expected replicate filename format is:

```text
<numeric_isolate>_rep<1|2|3>.mzXML
```

For example, `170_rep1.mzXML` represents isolate `170`, replicate `rep1`.

# Recommended workflow

1. Run `scan.py` against the raw directory. This creates the inventory and
   identifies missing replicates, duplicate replicate records, missing
   isolates, and hierarchy problems.
2. Review the CSV reports in `metadata/` before creating the organised copy.
3. Run `build_structure.py` to create isolate folders and copy or symlink the
   files listed in the inventory.
4. Run `log_Spectral_error.py` to test whether each organised mzXML file can be
   parsed and contains spectra and spectral peaks.
5. Run `countFiles.py` to summarise the number of files in each organised
   isolate folder.
6. Run `quick_pie.py` if a visual summary of file counts is useful.
7. Run `renmae_to_StrainID.py` only when the code-to-StrainID mapping is
   verified and the folder rename is intended.
8. Run `extrareplica.py` to import extra replicate files after their names and
   mapping have been checked.

The rename and import scripts change files and directories in place. Back up
the organised directory or use a copy of the project before running them.

# Script reference

## `scan.py`

### Purpose

Recursively scans the raw project directory for files ending in `.mzXML` and
builds the inventory used by the organisation step.

### Processing

- Uses the regular expression `^(\d+)_rep([123])\.mzXML$` to accept only
  numeric isolate IDs and replicates 1, 2, or 3.
- Records the batch directory, isolate, replicate, filename, parent replicate
  folder, hierarchy status, file size in megabytes, and absolute path.
- Marks `hierarchy_ok` as true only when the file is inside the matching
  `rep1`, `rep2`, or `rep3` folder.
- Sorts records numerically by isolate and then by replicate.
- Compares found isolates with the expected range 1 through 1053.
- Checks every found isolate for missing `rep1`, `rep2`, or `rep3` records.
- Detects duplicate isolate/replicate combinations.

### Outputs

- `metadata/isolate_inventory.csv`: the main inventory used by
  `build_structure.py`.
- `metadata/missing_replicates.csv`: expected replicates absent for an isolate.
- `metadata/duplicate_replicates.csv`: isolate/replicate combinations found
  more than once.
- `metadata/missing_isolates.csv`: isolate IDs from 1 to 1053 not found.
- `metadata/hierarchy_errors.csv`: files whose parent folder does not match
  their replicate value.
- `metadata/scan.log`: warnings for filenames that do not match the expected
  pattern.

If no filenames match, the script stops without producing a usable inventory.

## `build_structure.py`

### Purpose

Creates the `organised/` directory structure from the inventory. It does not
scan raw data directly; it trusts the paths and metadata in
`metadata/isolate_inventory.csv`.

### Processing

- Creates isolate folders `1` through `1053`.
- For each inventory row, maps `full_path` to the destination folder named for
  the isolate and uses the inventory `file_name` as the destination filename.
- Copies files with `shutil.copy2` by default, preserving file metadata.
- Can create symlinks instead by changing `COPY_MODE` from `copy` to
  `symlink`.
- Skips an existing destination unless `OVERWRITE = True`.
- Logs missing sources and copy errors, while continuing with other records.

### Outputs

- `organised/<isolate>/<file_name>`: copied or linked mzXML files.
- `organised/manifest.csv`: source, destination, isolate, and replicate for
  every inventory row attempted.
- `build_structure.log`: missing-source warnings and copy activity.

The manifest includes skipped and failed records because it is created from all
inventory rows before the copy operation.

## `log_Spectral_error.py`

### Purpose

Performs content-level QC on every mzXML file below the organised directory.
It is different from `scan.py`: `scan.py` checks names and hierarchy, while
this script opens each file and checks whether its spectral content is usable.

### Processing

- Walks the organised directory recursively.
- Opens each file with `pyteomics.mzxml.MzXML`.
- Counts spectra and sums the length of each available `m/z array`.
- Classifies files as `ok`, `no_spectra`, `empty_spectrum`, or `corrupt`.
- Treats parser exceptions as corrupt-file errors and continues scanning.

### Outputs

The script creates `metadata_spec_check/` and appends to these CSV logs:

- `corrupt_files_log.csv`: files that could not be parsed and the parser error.
- `warnings_log.csv`: files with no spectra, spectra with no peaks, or corrupt
  files.
- `qc_master_log.csv`: combined QC problem log with a normalised issue type.

The logs are append-only. Re-running the script against the same files can add
duplicate entries, so archive or remove old logs when a fresh QC report is
required.

## `countFiles.py`

### Purpose

Counts direct files in each immediate subdirectory of `organised/`.

### Processing and output

The script sorts isolate folders by folder name, counts files directly inside
each folder, totals all counts, and writes the result to
`organised/folder_file_counts.csv`. It does not recursively count files in
deeper subdirectories and includes the generated CSV itself if the script is
run again after that file already exists.

## `quick_pie.py`

### Purpose

Creates a pie chart showing how many isolate folders contain 1 file, 2 files,
3 files, and so on.

### Processing and output

Reads `folder_file_counts.csv`, removes rows with zero files, groups folders by
their file count, and saves a 300 DPI chart as
`folder_file_distribution_pie.png`. It also displays the chart with
`matplotlib.pyplot.show()`, so an interactive display may be required when the
script is run outside a notebook.

## `renmae_to_StrainID.py`

### Purpose

Replaces numeric isolate folder names and replicate filenames with values from
`code_ID.xlsx`.

### Processing

- Reads the `code` and `StrainID` columns and converts `code` values to strings.
- Expects existing folders to be named with numeric codes.
- Renames files matching `<code>_rep1.mzXML`, `<code>_rep2.mzXML`, or
  `<code>_rep3.mzXML` to `<StrainID>_rep<replicate>.mzXML`.
- Renames each mapped numeric folder to the corresponding StrainID folder.
- Skips folders whose code is absent from the mapping and reports them.

### Output and caution

Writes activity to `rename_to_strainID.log` and prints a summary. The filename
is intentionally retained as it exists in the project, although the word
`renmae` is misspelled in the script filename. The script does not explicitly
check whether a destination file or destination folder already exists before
renaming, so mapping collisions should be resolved first.

## `extrareplica.py`

### Purpose

Moves extra replicate files from `EXTRA_REPLICATE/` into the matching
StrainID folder under `organised/`.

### Processing

- Reads `code_ID.xlsx` and maps the `code` column to `StrainID`.
- Accepts extra files named `<numeric_code>_rep<number>.mzXML`.
- Looks up the numeric code, creates the destination StrainID folder if
  needed, and moves the file there as `<StrainID>_rep<number>.mzXML`.
- Skips an existing destination unless `OVERWRITE = True`.
- Records invalid names and codes missing from the mapping instead of moving
  them.

### Outputs

- `extra_replicates_manifest.csv`: code, StrainID, replicate, and destination
  for files moved during the run.
- `import_extra_replicates.log`: moved and skipped counts.

The regular expression allows any numeric replicate number, unlike the main
scanner and renaming script, which only accept replicates 1 through 3.

# Required inputs and dependencies

The scripts use Python 3 and the following packages:

- `pandas` for CSV and Excel tables.
- `matplotlib` for the pie chart.
- `pyteomics` for mzXML content QC.

The project also includes `environment.yml`, which should be used to recreate
the intended environment when possible. The mapping-dependent scripts require
`code_ID.xlsx` with columns named `code` and `StrainID`.

Before running the workflow, check these settings:

- `scan.py`: update `RAW_DIRECTORY` if the raw data is elsewhere.
- `log_Spectral_error.py`: update `SEARCH_FOLDER`, `METADATA_FOLDER`, and the
  log paths if the project is moved.
- `build_structure.py`: confirm `EXPECTED_ISOLATES`, `COPY_MODE`, and
  `OVERWRITE`.
- `renmae_to_StrainID.py` and `extrareplica.py`: confirm the mapping column
  names and the overwrite policy.

# Interpretation of the QC reports

Use the structural reports before trusting the organised directory:

- Missing isolates or replicates indicate incomplete coverage.
- Duplicate replicate rows can cause multiple sources to target the same
  destination.
- Hierarchy errors indicate that a file's location does not agree with its
  replicate name.
- Corrupt-file records indicate parser failures, while `no_spectra` and
  `empty_spectrum` indicate files that parse but do not contain usable signal.

The output CSV files and generated images are analysis products. The Python
source files and this R Markdown document describe the reproducible workflow;
large mzXML data files and generated logs should generally be managed outside
the source-code commit.
