import os
import shutil


for book in os.listdir("./output"):
    book_path = os.path.join("./output", book)
    for chapter in os.listdir(book_path):
        chapter_path = os.path.join(book_path, chapter)
        image_path = os.path.join(chapter_path, "graph.png")
        if not os.path.exists(image_path):
            continue
        dest_dir = "./output/graphs/"
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{book}_{chapter}.png")
        shutil.copy(image_path, dest_path)
        print(f"Copied {image_path} to {dest_path}")