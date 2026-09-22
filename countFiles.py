from pathlib import Path
import pandas as pd

# Change this to your organised folder
ROOT = Path("organised")

results = []

total_files = 0

for folder in sorted(
    [f for f in ROOT.iterdir() if f.is_dir()],
    key=lambda x: x.name
):

    n_files = sum(1 for f in folder.iterdir() if f.is_file())

    results.append({
        "Folder": folder.name,
        "Number_of_Files": n_files
    })

    total_files += n_files

# Create DataFrame
df = pd.DataFrame(results)

# Save to CSV
output_file = ROOT / "folder_file_counts.csv"
df.to_csv(output_file, index=False)

# Print summary
print("=" * 50)
print("Folder count completed")
print("=" * 50)
print(f"Folders scanned : {len(df)}")
print(f"Total files     : {total_files}")
print(f"CSV written to  : {output_file}")