
from pypdf import PdfReader

reader = PdfReader("Seconde_Fondation_sample.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

print(text, file=open("Seconde_Fondation_sample.txt", "w", encoding="utf-8"))