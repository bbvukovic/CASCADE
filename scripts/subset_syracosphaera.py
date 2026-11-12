##creating a subset of the gridded abundances dataset (that has data from the 2 additional cruises) which keeps only rows where Syracosphaera species appear

import pandas as pd
from pathlib import Path

input_file = Path(
    r"C:\Users\borna\Documents\GitHub\CASCADE\data\output\gridded_abundances.csv"
)

output_file = Path(
    r"C:\Users\borna\Documents\GitHub\CASCADE\data\output\gridded_abundances_syracosphaera_nonzero.csv"
)

# Read CASCADE output
df = pd.read_csv(input_file)

print("Original rows:", len(df))

# Find all Syracosphaera abundance columns
syracosphaera_cols = [
    col for col in df.columns
    if "Syracosphaera" in col
]

print("\nSyracosphaera taxa found:")
for col in syracosphaera_cols:
    print(col)

print("\nNumber of Syracosphaera taxa:", len(syracosphaera_cols))


# Keep rows where at least one Syracosphaera taxon
# has an abundance greater than zero
syracosphaera = df[
    (df[syracosphaera_cols] > 0).any(axis=1)
].copy()

print("\nRows containing Syracosphaera:", len(syracosphaera))


# Check number of unique environmental sampling points

sampling_cols = [
    "Latitude",
    "Longitude",
    "Depth",
    "Month",
    "Year"
]

print(
    "\nUnique environmental sampling points:",
    len(syracosphaera[sampling_cols].drop_duplicates())
)
# Save
syracosphaera.to_csv(output_file, index=False)

print("\nSaved to:")
print(output_file)