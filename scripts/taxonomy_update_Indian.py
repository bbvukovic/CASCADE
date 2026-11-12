import pandas as pd
import yaml

# --------------------------------------------------
# File paths
# --------------------------------------------------

mapping_path = "./scripts/TN376_taxonomy_mapping.csv"
synonyms_path = "./data/classification/synonyms.yml"


# --------------------------------------------------
# 1. Read curated TN376 taxonomy mapping
# --------------------------------------------------

mapping = pd.read_csv(mapping_path)

print("Number of TN376 taxa:", len(mapping))


# --------------------------------------------------
# 2. Determine final canonical CASCADE name
#
# final_CASCADE_name = manually curated name
# CASCADE_name       = taxa already recognized by CASCADE
# --------------------------------------------------

mapping["target_CASCADE_name"] = (
    mapping["final_CASCADE_name"]
    .fillna(mapping["CASCADE_name"])
)

unresolved = mapping[
    mapping["target_CASCADE_name"].isna()
]

if len(unresolved) > 0:
    print("\nERROR: Some taxa still have no final CASCADE name:")
    print(unresolved["TN376_name"].to_string(index=False))
    raise ValueError(
        "Unresolved taxa remain. synonyms.yml was NOT modified."
    )

print("All TN376 taxa have a final CASCADE name.")


# --------------------------------------------------
# 3. Load existing CASCADE synonym dictionary
# --------------------------------------------------

with open(synonyms_path, "r", encoding="utf-8") as file:
    synonyms = yaml.safe_load(file)


# --------------------------------------------------
# 4. Add TN376 names to synonym dictionary
# --------------------------------------------------

added_synonyms = []
already_present = []
new_canonical_taxa = []

for _, row in mapping.iterrows():

    tn376_name = str(row["TN376_name"]).strip()
    cascade_name = str(row["target_CASCADE_name"]).strip()

    # ----------------------------------------------
    # Existing canonical CASCADE taxon
    # ----------------------------------------------

    if cascade_name in synonyms:

        if synonyms[cascade_name] is None:
            synonyms[cascade_name] = []

        if tn376_name not in synonyms[cascade_name]:
            synonyms[cascade_name].append(tn376_name)

            added_synonyms.append(
                (tn376_name, cascade_name)
            )

        else:
            already_present.append(
                (tn376_name, cascade_name)
            )

    # ----------------------------------------------
    # New canonical taxon introduced by TN376
    # ----------------------------------------------

    else:

        synonyms[cascade_name] = [tn376_name]

        new_canonical_taxa.append(
            (cascade_name, tn376_name)
        )


# --------------------------------------------------
# 5. Print summary BEFORE writing
# --------------------------------------------------

print("\n--------------------------------")
print("Existing taxa: new synonyms added")
print("--------------------------------")

for tn376_name, cascade_name in added_synonyms:
    print(f"{tn376_name}  ->  {cascade_name}")


print("\n--------------------------------")
print("Already present")
print("--------------------------------")

for tn376_name, cascade_name in already_present:
    print(f"{tn376_name}  ->  {cascade_name}")


print("\n--------------------------------")
print("NEW canonical CASCADE taxa")
print("--------------------------------")

for cascade_name, tn376_name in new_canonical_taxa:
    print(f"{cascade_name}")
    print(f"    synonym: {tn376_name}")


print("\nSummary:")
print("Added synonyms:", len(added_synonyms))
print("Already present:", len(already_present))
print("New canonical taxa:", len(new_canonical_taxa))


# --------------------------------------------------
# 6. Write updated synonyms.yml
# --------------------------------------------------

with open(synonyms_path, "w", encoding="utf-8") as file:
    yaml.safe_dump(
        synonyms,
        file,
        sort_keys=False,
        allow_unicode=True
    )

print("\nUpdated:")
print(synonyms_path)