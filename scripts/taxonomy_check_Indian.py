import pandas as pd
import yaml
import re
from difflib import get_close_matches

def simplify_taxon_name(name):
    """
    Extract genus + species for candidate matching only.

    This does NOT modify the original taxonomy.
    """

    name = str(name).strip()

    words = name.split()

    if len(words) >= 2:
        return " ".join(words[:2])

    return name

# --------------------------------------------------
# File paths
# --------------------------------------------------

excel_path = "./data/unprocessed/abundances/TN376_Indian.xlsx"
synonyms_path = "./data/classification/synonyms.yml"


# --------------------------------------------------
# 1. Read TN376
# --------------------------------------------------

df = pd.read_excel(
    excel_path,
    sheet_name="Cells_Liter"
)

print("TN376 dimensions:", df.shape)

# --------------------------------------------------
# Read TN376 species information
# --------------------------------------------------

species_info = pd.read_excel(
    excel_path,
    sheet_name="Species"
)

species_info = species_info[
    ["Name", "2n/n"]
].rename(
    columns={
        "Name": "TN376_name",
        "2n/n": "Phase"
    }
)

species_info["TN376_name"] = species_info["TN376_name"].str.strip()
species_info["Phase"] = species_info["Phase"].str.strip()

print("\nLife-cycle phases in Species sheet:")
print(species_info["Phase"].value_counts())

# --------------------------------------------------
# 2. Identify species columns
# --------------------------------------------------

metadata_columns = [
    "Station",
    "Longitude",
    "Latitude",
    "Date",
    "Depth"
]

species_columns = [
    col for col in df.columns
    if col not in metadata_columns
]

print("Number of taxon columns:", len(species_columns))


# --------------------------------------------------
# 3. Read CASCADE synonym dictionary
# --------------------------------------------------

with open(synonyms_path, "r", encoding="utf-8") as file:
    synonyms = yaml.safe_load(file)


# --------------------------------------------------
# 4. Build reverse lookup:
#    synonym -> CASCADE canonical name
# --------------------------------------------------

synonym_lookup = {}

for canonical_name, synonym_list in synonyms.items():

    # The canonical name itself should also be recognised
    synonym_lookup[canonical_name] = canonical_name

    # Add all synonyms belonging to that canonical name
    if synonym_list is not None:
        for synonym in synonym_list:
            synonym_lookup[str(synonym)] = canonical_name

# --------------------------------------------------
# 5. Build a second lookup using simplified names
# --------------------------------------------------

simplified_lookup = {}

for name, canonical_name in synonym_lookup.items():

    simplified_name = simplify_taxon_name(name)

    if simplified_name not in simplified_lookup:
        simplified_lookup[simplified_name] = []

    if canonical_name not in simplified_lookup[simplified_name]:
        simplified_lookup[simplified_name].append(canonical_name)

# --------------------------------------------------
# 6. Compare TN376 taxa with CASCADE taxonomy
# --------------------------------------------------

results = []

for taxon in species_columns:

    # Get phase information from Species sheet
    phase_matches = species_info.loc[
        species_info["TN376_name"] == taxon,
        "Phase"
    ].unique()

    if len(phase_matches) == 1:
        tn376_phase = phase_matches[0]

    elif len(phase_matches) > 1:
        tn376_phase = " | ".join(phase_matches)

    else:
        tn376_phase = None

    # Simplify taxon name for CASCADE comparison
    simplified_taxon = simplify_taxon_name(taxon)

    # Compare with CASCADE taxonomy
    if taxon in synonyms:
        status = "Direct canonical match"
        cascade_name = taxon
        suggested_match = None

    elif taxon in synonym_lookup:
        status = "Synonym match"
        cascade_name = synonym_lookup[taxon]
        suggested_match = None

    elif simplified_taxon in simplified_lookup:

        candidates = simplified_lookup[simplified_taxon]

        # Filter CASCADE candidates using TN376 phase
        phase_filtered_candidates = candidates.copy()

        # Only filter when TN376 has one unambiguous phase
        if tn376_phase in ["HET", "HOL", "COM", "POL"]:

            matching_phase = [
                candidate for candidate in candidates
                if tn376_phase.upper() in candidate.upper()
            ]

            # Only use filtering if it found something
            if len(matching_phase) > 0:
                phase_filtered_candidates = matching_phase

        # Evaluate remaining candidates
        if len(phase_filtered_candidates) == 1:
            status = "Suggested match - review"
            cascade_name = None
            suggested_match = phase_filtered_candidates[0]

        else:
            status = "Multiple possible matches - review"
            cascade_name = None
            suggested_match = " | ".join(phase_filtered_candidates)

    else:
        status = "No match"
        cascade_name = None
        suggested_match = None

    results.append({
        "TN376_name": taxon,
        "TN376_phase": tn376_phase,
        "simplified_name": simplified_taxon,
        "status": status,
        "CASCADE_name": cascade_name,
        "suggested_match": suggested_match
    })


results = pd.DataFrame(results)

# --------------------------------------------------
# 7. Print results
# --------------------------------------------------

print("\nTaxonomy comparison:\n")
print(results.to_string(index=False))


# --------------------------------------------------
# 8. Save results
# --------------------------------------------------

results.to_csv(
    "./TN376_taxonomy_check.csv",
    index=False
)

print("\nSaved results to TN376_taxonomy_check.csv")

# --------------------------------------------------
# 9. Export taxa that still need manual review
# --------------------------------------------------

unresolved = results[
    results["status"].isin([
        "Multiple possible matches - review",
        "No match"
    ])
].copy()

unresolved.to_csv(
    "./TN376_taxonomy_unresolved.csv",
    index=False
)

print(
    f"\nSaved {len(unresolved)} unresolved taxa "
    "to TN376_taxonomy_unresolved.csv"
)