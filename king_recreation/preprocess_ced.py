import csv
import re
import os

def clean_string(s):
    if not s or s == "-----":
        return ""
    # Remove tones [1234] and glottal stops [?] and periods [.]
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    return re.sub(r'[1234\.\?]', '', s)

def clean_row(row):
    definition = row.get("definition", "").strip()
    
    present = clean_string(row.get("3rd present", ""))
    
    imperfective_raw = row.get("3rd incompletive habitual", "")
    imperfective = clean_string(imperfective_raw)
    # README: "3rd incompletive habitual column with oi rstripped"
    # Logic: if it ends in 'i' (possibly with tones/glottals), and has 'o' before it.
    if imperfective.endswith("oi"):
        imperfective = imperfective[:-2]
    
    perfective_raw = row.get("3rd completive past", "")
    perfective = clean_string(perfective_raw)
    # README: "3rd completive past column with vi rstripped"
    if perfective.endswith("vi"):
        perfective = perfective[:-2]
        
    imperative = clean_string(row.get("2nd imperative", ""))
    
    infinitive_raw = row.get("3rd infinitive", "")
    infinitive = clean_string(infinitive_raw)
    # README: "3rd infinitive column with i rstripped"
    if infinitive.endswith("i"):
        infinitive = infinitive[:-1]
        
    return {
        "definition": definition,
        "present": present,
        "imperfective": imperfective,
        "perfective": perfective,
        "imperative": imperative,
        "infinitive": infinitive
    }

def process_ced():
    input_path = "data/ced_data_original.csv"
    output_dir = "artifacts"
    output_path = os.path.join(output_dir, "corpus.csv")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    processed_data = []

    with open(input_path, mode='r', encoding='utf-8') as f:
        # The file seems to have a trailing comma in the header based on initial view
        reader = csv.DictReader(f)
        for row in reader:
            processed_data.append(clean_row(row))

    fieldnames = ["definition", "present", "imperfective", "perfective", "imperative", "infinitive"]
    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)

    print(f"Processed data written to {output_path}")

if __name__ == "__main__":
    process_ced()
