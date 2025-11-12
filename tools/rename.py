# rename all files in text_dataset if they are starting with lca. or paf. tothe number before.
# example:
# lca.chapter_1.txt  ->  lca.chapter_0.txt
# lca.chapter_2.txt  ->  lca.chapter_1.txt
# paf.chapter_1.txt  ->  paf.chapter_0.txt
# etc.

# store the new files in text_dataset_renamed

import os
import re
import glob
import shutil

def rename_files_in_directory(directory):
    # Create the new directory if it doesn't exist
    new_directory = directory + "_renamed"
    os.makedirs(new_directory, exist_ok=True)

    # Get all files starting with lca. or paf.
    files = glob.glob(os.path.join(directory, 'lca.*')) + glob.glob(os.path.join(directory, 'paf.*'))

    for file_path in files:
        file_name = os.path.basename(file_path)
        
        # Match the pattern and extract the prefix and number
        match = re.match(r'^(lca|paf)\.chapter_(\d+)(.*)$', file_name)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            suffix = match.group(3)

            # Decrement the chapter number by 1
            new_number = number - 1
            new_file_name = f"{prefix}.chapter_{new_number}{suffix}"
            new_file_path = os.path.join(new_directory, new_file_name)

            # Copy the file to the new directory with the new name
            shutil.copy(file_path, new_file_path)
            print(f"Renamed: {file_name} -> {new_file_name}")
        else:
            print(f"Skipping file (no match): {file_name}")
    
if __name__ == "__main__":
    rename_files_in_directory('text_dataset')