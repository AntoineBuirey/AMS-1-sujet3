import nltk
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize

# Téléchargement des modèles NLTK (une seule fois)
nltk.download('punkt')
nltk.download('punkt_tab')

# --- Lire le texte du fichier ---
with open("Fondation_et_empire_sample.txt", "r", encoding="utf-8") as f:
    texte = f.read()

# --- Découper en phrases ---
phrases = sent_tokenize(texte, language="french")

# --- Créer le fichier de sortie ---
with open("corpus.txt", "w", encoding="utf-8") as f_out:
    for phrase in phrases:
        mots = word_tokenize(phrase, language="french")

        f_out.write("============\n")
        f_out.write(phrase.strip() + "\n")
        f_out.write("============\n")
        for mot in mots:
            f_out.write(f"- {mot}\n")
        f_out.write("\n") 
