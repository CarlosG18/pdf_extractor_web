import os
import re
import fitz
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from pytesseract import pytesseract
from io import BytesIO
import traceback
from PIL import Image, ImageFilter, ImageOps

def check_match_page(page_data, page_number, flag=False):
    """
        função para verificar se o texto da pagina bate com o padrão regex

        - args:
           - page_data: dados da pagina
           - page_number: número da pagina
           - flag: flag para aplicar o pré-processamento da imagem ou não

        - return: boolean
    """
    text = pytesseract.image_to_string(page_data).encode("utf-8")
    text_bytes = text.decode('utf-8')

    print(text_bytes)


pytesseract.tesseract_cmd = r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\include\Tesseract-OCR\tesseract'
path_poppler = r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\include\poppler-23.07.0\Library\bin'

for i in range(4):
    print(f"-----------  optimize = {i} ---------------")
    # Lendo o documento PDF
    doc = convert_from_path(fr'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\documento_com_ocr{i}.pdf', poppler_path=path_poppler)

    for page_number, page_data in enumerate(doc):
        is_not_match = check_match_page(page_data, page_number)
                
        if is_not_match:
            is_not_match = check_match_page(page_data, page_number, flag=True) 