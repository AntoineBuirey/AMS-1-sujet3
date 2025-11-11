import os
import shutil


def copy_items(filename : str):
    name_noext, ext = os.path.splitext(filename)
    for book in os.listdir("./output"):
        book_path = os.path.join("./output", book)
        for chapter in os.listdir(book_path):
            chapter_path = os.path.join(book_path, chapter)
            image_path = os.path.join(chapter_path, filename)
            if not os.path.exists(image_path):
                continue
            dest_dir = f"./output/{name_noext}/"
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, f"{book}_{chapter}.{ext.lstrip('.')}")
            shutil.copy(image_path, dest_path)
            print(f"Copied {image_path} to {dest_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Copy result items (images, graphml) from output folders to a single folder.")
    parser.add_argument("filename", type=str, help="Name of the file to copy (e.g., graph.png, graph.graphml).")
    args = parser.parse_args()
    copy_items(args.filename)