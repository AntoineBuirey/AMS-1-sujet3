import spacy
import nltk
from nltk.tokenize import sent_tokenize

# Charger le modèle français de spaCy
nlp = spacy.load("fr_core_news_sm")

# Lire le fichier texte
with open("mon_texte.txt", "r", encoding="utf-8") as f:
    texte = f.read()

# Découper en phrases
nltk.download('punkt')
nltk.download('punkt_tab')
phrases = sent_tokenize(texte, language="french")

with open("noms_propres.txt", "w", encoding="utf-8") as f_out:
    for phrase in phrases:
        doc = nlp(phrase)

        # ➡️ Extraire uniquement les noms propres
        noms_propres = [token.text for token in doc if token.pos_ == "PROPN"]

        f_out.write("============\n")
        f_out.write(phrase.strip() + "\n")
        f_out.write("============\n")
        for nom in noms_propres:
            f_out.write(f"- {nom}\n")
        f_out.write("\n")
