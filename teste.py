import os
import ocrmypdf
import subprocess

# Define o caminho do tesseract manualmente
os.environ['PATH'] += os.pathsep + os.path.abspath("include/Tesseract-OCR")
os.environ['PATH'] += os.pathsep + os.path.abspath("include/pngquant")
os.environ['PATH'] += os.pathsep + r"C:\Program Files\gs\gs10.02.1\bin"

input_pdf = "documento_escaneado.pdf"
output_pdf = "documento_com_ocr.pdf"

for i in range(4):
    ocrmypdf.ocr(
        input_pdf,
        f"documento_com_ocr{i}.pdf",
        language='por',
        deskew=True,
        optimize=i,
        progress_bar=True
    )