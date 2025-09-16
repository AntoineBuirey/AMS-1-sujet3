import re
import nltk
import argparse
import os
import json
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize

parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
args = parser.parse_args()

with open(f"text_dataset/{args.input_file}", "r", encoding="utf-8") as f:
    text = f.read()
    
# same file name, but in the output folder
output_file = os.path.join("output", os.path.basename(args.input_file))
output_file = output_file.replace(".txt", ".raw.json")

sentences = re.split(r'(?<=[a-zA-Z )"]{2}[.!?]) +|"|- \d -', text)

result = []
for i in range(len(sentences)):
    sentence = sentences[i].strip(" \n\t\r-")
    if sentence == "":
        continue
    
    mots = word_tokenize(sentence, language="french")
    # print("==============================")
    # print(mots)
    result.append(mots)

os.makedirs("output", exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(result, f_out, ensure_ascii=False, indent=4)
print(f"Tokenized sentences written to {output_file}")
