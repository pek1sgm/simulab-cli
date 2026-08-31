import fitz
import os

SRC_DIR = r"c:\Users\pek1sgm\Desktop\simulab-doku"
OUT_DIR = r"C:\Users\pek1sgm\AppData\Local\Temp\simulab-pdf-pages"
os.makedirs(OUT_DIR, exist_ok=True)

ZOOM = 3.0
mat = fitz.Matrix(ZOOM, ZOOM)

for i in range(10):
    path = f"{SRC_DIR}\\{i}.pdf"
    doc = fitz.open(path)
    for p in range(doc.page_count):
        page = doc[p]
        pix = page.get_pixmap(matrix=mat)
        out_path = os.path.join(OUT_DIR, f"{i}_{p+1}.png")
        pix.save(out_path)
        print(out_path, pix.width, pix.height)
    doc.close()
