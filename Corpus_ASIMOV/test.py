
from pypdf import PdfReader

reader = PdfReader("Fondation_et_empire_sample.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

print(text, file=open("output.txt", "w", encoding="utf-8"))