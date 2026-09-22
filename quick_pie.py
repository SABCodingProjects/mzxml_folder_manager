import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV
df = pd.read_csv("folder_file_counts.csv")

# Remove folders with zero files
df = df[df["Number_of_Files"] > 0]

# Count how many folders have 1, 2, 3, 4, 5... files
counts = (
    df["Number_of_Files"]
    .value_counts()
    .sort_index()
)

# Create labels
labels = [f"{i} file{'s' if i > 1 else ''}" for i in counts.index]

# Plot
plt.figure(figsize=(7, 7))

plt.pie(
    counts,
    labels=labels,
    autopct="%1.1f%%",
    startangle=90
)

plt.title("Distribution of Number of Files per Isolate")

plt.axis("equal")

plt.tight_layout()

plt.savefig(
    "folder_file_distribution_pie.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Pie chart saved as folder_file_distribution_pie.png")