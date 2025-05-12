from .forms import BBForms, SICREDIForms, RecibosPagForms, ImpostoRendaForms, SomaPayForms, ScannerForms
from django.contrib import messages
from django.shortcuts import render, redirect
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

import ocrmypdf

os.environ['PATH'] += os.pathsep + os.path.abspath("include/Tesseract-OCR")
os.environ['PATH'] += os.pathsep + os.path.abspath("include/pngquant")
os.environ['PATH'] += os.pathsep + os.path.abspath("include/gs10.05.0/bin")

nfe = {}
pages_not_match = []

def preprocess_image(image: Image.Image) -> Image.Image:
    """
        Pré-processamento da imagem para melhorar OCR.
    """
    gray = image.convert("L")
    contrast = ImageOps.autocontrast(gray)
    binarized = contrast.point(lambda x: 0 if x < 128 else 255, "1")
    filtered = binarized.filter(ImageFilter.MedianFilter(size=3))
    return filtered

def check_forms(request, forms, tipo_arquivo):
    """
        função para checar se os dados do formulario são validos e passar para a função que faz o tratamento

        - args:
            - request: requisição atual;
            - forms: formulario ao qual os dados serão validados
            - tipo_arquivo: string para diferenciação dos tipos de arquivos
        
        - return: None ou redirecionamento para a pagina index se o formato do arquivo não for em pdf
    """
    # resetando a variavel nfe
    nfe = {}

    if forms.is_valid():
        doc = forms.cleaned_data[f"arquivo_{tipo_arquivo}"]

        # Validação para o tipo de arquivo (PDF)
        if not doc.name.endswith('.pdf'):
            messages.error(request, "O arquivo não é do formato PDF!")
            return redirect('index')

        output_folder = forms.cleaned_data[f"path_{tipo_arquivo}"]
        
        # abrindo o arquivo enviado é alocado na pasta midia usando o chuncks (pegando o conteudo do arquivo aos poucos)
        with open(f'midia/{doc.name}', 'wb+') as destination:
            for chunk in doc.chunks():
                destination.write(chunk)
        
        try:
            if tipo_arquivo == "scanner":
                split_pdf_by_employee_scanner(request, f'midia/{doc.name}', output_folder)
            else:
                split_pdf_by_employee(request, f'midia/{doc.name}', output_folder, tipo_arquivo)
        except Exception as e:
            error_message = f"Erro ao separar os {tipo_arquivo}s: {str(e)}"
            print(error_message)  # ou use logging.error(error_message)
            traceback.print_exc()  # imprime o stack trace no terminal
            messages.error(request, error_message)
            return redirect('index')
    else:
        messages.error(request, "arquivo ou caminho vazios!")
        return redirect('index')

def check_match_page(page_data, page_number, flag=False):
    """
        função para verificar se o texto da pagina bate com o padrão regex

        - args:
           - page_data: dados da pagina
           - page_number: número da pagina
           - flag: flag para aplicar o pré-processamento da imagem ou não

        - return: boolean
    """

    global nfe
    global pages_not_match
    match_regex = True
    
    if flag:
        processed_img = preprocess_image(page_data)  # Pré-processa a imagem
        text = pytesseract.image_to_string(processed_img).encode("utf-8")
    else:
        text = pytesseract.image_to_string(page_data).encode("utf-8")
    text_bytes = text.decode('utf-8')

    #print(f"------pagina: {page_number}--------")
    #print(text_bytes)

    if page_number == 4:
        #print(flag)
        print(f"------pagina: {page_number}--------")
        print(text_bytes)
        pass

    #criando uma lista de regex para pegar o nome do colaborador
    regex_list = [
        r"Empregado:\s\d+\s*-\s*([A-ZÀ-Ú ]+)\s*Peri",
        r"Empregado:\s\d+\s([A-ZÀ-Ú ]+)\s*Periodo",
        r"Empregado:\n\n\d+\n\n\d+\s-\n\n([A-ZÀ-Ú ]+)",
        r"Empregado:\n\n\d+\n\n([A-ZÀ-Ú ]+)",
        r"Empregado:\s\d+\s-\s([A-ZÀ-Ú ]+)",
        r"Empregado:\s\d+\n\n([A-ZÀ-Ú ]+)",
        r"Empregado:\n\n([A-ZÀ-Ú ]+)",
        r"Empregado:\s\d+\s([A-ZÀ-Ú ]+)",
        r"Empregado:\n\n([A-ZÀ-Ú ]+)",
        r"([A-ZÀ-Ú ]+)\n\d{2}/\d{2}/\d{4}",
        r"\d+\s-\s([A-ZÀ-Ú ]+)\s*Periodo",
        r"d+\s=\s([A-ZÀ-Ú ]+)",
        r"([A-Za-zÀ-ÿ ]+)\n\d{3}\.\d{3}\.\d{3}-\d{2}",
        r":\s-\s([A-ZÀ-Ú ]+)\sPeriodo",
        r"([A-ZÀ-Ú ]+)\s+",
    ]

    for regex in regex_list:
        name_pattern = re.compile(regex, re.MULTILINE)
        match = name_pattern.search(text_bytes)
        
        if match:
            #print(f"Page {page_number} - match.")
            match_regex = False
            beneficiario_name = match.group(1).strip()
            #print(beneficiario_name)
            # Cria uma entrada para o beneficiário se não existir
            if beneficiario_name not in nfe:
                nfe[beneficiario_name] = []
            nfe[beneficiario_name].append(page_number)
            #print(f"page number: {page_number} - regex usado {regex} - nome do colaborador: {beneficiario_name}")
            break
        else:
            pages_not_match.append(page_number)
            #print(f"Page {page_number} - No match found.")

    return match_regex

def split_pdf_by_employee_scanner(request, input_pdf_path, output_folder):
    """
        função para separar os arquivos em pdf de acordo com o nome do colaborador - scanner

        - args:
            - input_pdf_path: caminho do pdf
            - output_folder: caminho da pasta onde os arquivos serão criados

        - return: None
    """
    global nfe
    global pages_not_match
    pytesseract.tesseract_cmd = r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\include\Tesseract-OCR\tesseract'
    path_poppler = r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\include\poppler-23.07.0\Library\bin'

    # Verificando se o arquivo de saída existe,
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Lendo o documento PDF
    try:
        #doc = convert_from_path(r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\midia\pdf-process.pdf', poppler_path=path_poppler)
        doc = convert_from_path(input_pdf_path, poppler_path=path_poppler)
    except:
        messages.error(request, "Erro na aquisição das imgens pelo pdf!")
        return redirect('index')

    is_not_match = True

    for page_number, page_data in enumerate(doc):
        is_not_match = check_match_page(page_data, page_number)
        #print(page_number, is_not_match)
              
        if is_not_match:
           is_not_match = check_match_page(page_data, page_number, flag=True) 
  
    # Salva cada beneficiário em um PDF separado
    for beneficiario, pages in nfe.items():
        output_pdf_path = os.path.join(output_folder, f'{beneficiario}.pdf')

        # Cria um novo PDF
        new_doc = fitz.open()

        for index in pages:
            #print(doc[index])
            img = doc[index]  # Obtém a imagem da página correspondente

            # Converte a imagem para bytes
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Salva a imagem em um stream JPEG válido
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)

            # Obtém as dimensões da imagem
            img_width, img_height = img.size

            # Cria a página no PDF
            page = new_doc.new_page(width=img_width, height=img_height)

            # Insere a imagem na nova página
            rect = fitz.Rect(0, 0, img_width, img_height)
            page.insert_image(rect, stream=img_byte_arr.read())

        new_doc.save(output_pdf_path)  # Salva o novo PDF
        new_doc.close()  # Fecha o novo PDF

    # usando outra ferramenta para as paginas que o regex não bateu
    #print(f"is_not_match = {is_not_match}")
    #print(set(pages_not_match))

    set_pages_not_match = set(pages_not_match)

    print(set_pages_not_match)

    os.remove(input_pdf_path)
    #os.remove(r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\midia\pdf-process.pdf')

    #mensagens de feedback para o usuário
    if is_not_match:
        messages.error(request, "O regex aplicado não esta nos padrões do PDF carregado!")
    else:
        messages.success(request, f"comprovantes/recibos separados com sucesso!")
        

# Create your views here.
def split_pdf_by_employee(request, input_pdf_path, output_folder, tipo_arquivo):
    """
        função para separar os arquivos em pdf de acordo com o nome do colaborador

        - args:
            - input_pdf_path: caminho do pdf
            - output_folder: caminho da pasta onde os arquivos serão criados
            - tipo_arquivo: o tipo de comprovante podendo ser do tipo BB, SICREDI

        - return: None
    """

    # Verificando se o arquivo de saída existe,
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Lendo o documento PDF
    doc = fitz.open(input_pdf_path)

    #total_pages = doc.page_count
    cont = 0
    nfe = {}
    pages_not_match = []
    page_prev = 0
    beneficiario_name_current = ''

    is_not_match = True

    for page in doc:  # Itera pelas páginas do documento
        text = page.get_text().encode("utf-8")  # Obtém o texto em UTF-8
        text_bytes = text.decode('utf-8')

        current_page = page.number
        #print(page.number)

        if current_page == 0:
            page_prev = current_page

        # aplicando a regra para o tipo de comprovante - BB
        if tipo_arquivo == "BB":
            name_pattern = re.compile(r'BENEFICIARIO:\s+(.+)')
        # aplicando a regra para o tipo de comprovante - SICREDI
        if tipo_arquivo == "SICREDI":
            name_pattern = re.compile(r'CPF\/CNPJ:\s*\n(.*)')
        ## aplicando a regra para o tipo de comprovante - Recibos de pagamento
        if tipo_arquivo == "recibos_pag":
            name_pattern = re.compile(r"\d{6}\s+([a-zA-Z ]+)")
        ## aplicando a regra para o tipo de comprovante - Imposto de Renda
        if tipo_arquivo == "imposto_renda":
            name_pattern = re.compile(r"Nome Completo\s*\d{3}\.\d{3}\.\d{3}-\d{2}\s*([A-ZÁÀÂÃÉÈÍÌÓÒÚÙÇÑ ]+)")
        ## aplicando a regra para o tipo de comprovante - SomaPay
        
        match = name_pattern.search(text_bytes) # pattern relacionada ao comprovante

        if match:
            page_prev = current_page
            is_not_match = False
            beneficiario_name = match.group(1).strip()
            beneficiario_name_current = beneficiario_name
            # Cria uma entrada para o beneficiário se não existir
            if beneficiario_name not in nfe:
                nfe[beneficiario_name] = []
            nfe[beneficiario_name].append(page)
        else:
            #print(current_page, page_prev)
            # if current_page - page_prev == 1:
            #     #print(f"Page {current_page} Adding to {beneficiario_name_current}.")
            #     nfe[beneficiario_name_current].append(page)
            # else:
            #     pages_not_match.append(page)
            pages_not_match.append(page)
            
    # Salva cada beneficiário em um PDF separado
    for beneficiario, pages in nfe.items():
        output_pdf_path = os.path.join(output_folder, f'{beneficiario}.pdf')

        # Cria um novo PDF
        new_doc = fitz.open()
        
        for page in pages:
            new_doc.insert_pdf(doc, from_page=page.number, to_page=page.number)

        new_doc.save(output_pdf_path)  # Salva o novo PDF
        new_doc.close()  # Fecha o novo PDF

    #print(f'Páginas que não correspondem a nenhum beneficiário: {len(pages_not_match)}')
    output_folder_not_match = r'C:\Users\carlos.medeiros\carlos\projetos-conectrom\extrator-web\not_match'
    # Salva as páginas que não correspondem a nenhum beneficiário
    for page in pages_not_match:
        output_pdf_path = os.path.join(output_folder_not_match, f'{page.number}.pdf')
        no_match = fitz.open()

        no_match.insert_pdf(doc, from_page=page.number, to_page=page.number)
        no_match.save(output_pdf_path)  # Salva o PDF original
        no_match.close()

    doc.close()  # Fecha o PDF original
    os.remove(input_pdf_path)

    #mensagens de feedback para o usuário
    if is_not_match:
        messages.error(request, "O PDF carregado não esta nos padrões de leitura do extrator!")
    else:
        messages.success(request, f"comprovantes/recibos separados com sucesso!")

def index(request):
    """
        view para tratamento do arquivos
    """
    if request.method == 'POST':
        # obtendo os dados do forms passados pela requisição
        form_BB = BBForms(request.POST, request.FILES)
        form_SICREDI = SICREDIForms(request.POST, request.FILES)
        form_recibos_pag = RecibosPagForms(request.POST, request.FILES)
        form_imposto_renda = ImpostoRendaForms(request.POST, request.FILES)
        form_somapay = SomaPayForms(request.POST, request.FILES)
        form_scanner = ScannerForms(request.POST, request.FILES)
        
        tipo = request.POST["tipo_arquivo"]

        # validando os dados e realizando o processamento dos arquivos
        if tipo == "1":
            check_forms(request, form_BB, 'BB')
        elif tipo == "2":    
            check_forms(request, form_SICREDI, "SICREDI")
        elif tipo == "3":
            check_forms(request, form_recibos_pag, "recibos_pag")
        elif tipo == "4":
            check_forms(request, form_imposto_renda, "imposto_renda")
        elif tipo == "5":
            check_forms(request, form_somapay, "somapay")
        elif tipo == "6":
            check_forms(request, form_scanner, "scanner")
        
    else:
        form_BB = BBForms()
        form_SICREDI = SICREDIForms()
        form_recibos_pag = RecibosPagForms()
        form_imposto_renda = ImpostoRendaForms()
        form_somapay = SomaPayForms()
        form_scanner = ScannerForms()

    return render(request, 'index.html', {
        'form_BB': form_BB,
        'form_SICREDI': form_SICREDI,
        'form_recibos_pag': form_recibos_pag,
        'form_imposto_renda': form_imposto_renda,
        'form_somapay': form_somapay,
        'form_scanner': form_scanner,
    })