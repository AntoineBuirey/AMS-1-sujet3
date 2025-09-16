import re
import nltk
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize

with open("Corpus_ASIMOV/Fondation_foudroyée_sample.txt", "r", encoding="utf-8") as f:
    text = f.read()

# sentences = text.split(". ")

sentences = re.split(r'(?<=[a-zA-Z )"]{2}[.!?]) +|"|- \d -', text)
for i in range(len(sentences)):
    sentence = sentences[i].strip()
    if sentence == "":
        continue
    print("==============================")
    
    mots = word_tokenize(sentence, language="french")
    print(mots)
