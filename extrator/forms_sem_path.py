from django import forms
from django.conf import settings
import os
from pathlib import Path

user_path = os.path.join(os.path.expanduser("~"), 'documents')

#Lista de diretórioss permitidos para salvar arquivos
DIRECTORY_CHOICES = []

# Diretorios base onde os arquivos podem ser salvos
BASE_DIRS = [
    user_path,
]

# Gerar as opções de diretorios
for directory in BASE_DIRS:
    if os.path.exists(directory):
        # Opção diretorio principal
        rel_path = user_path
        DIRECTORY_CHOICES.append((rel_path, rel_path))
        
        # opções para subdiretorios
        for subdir in [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]:
            subdir_path = os.path.join(rel_path, subdir)
            DIRECTORY_CHOICES.append((subdir_path, subdir_path))

# Gerar uma opção padrão para o caso não haver o diretorio.
if not DIRECTORY_CHOICES:
    DIRECTORY_CHOICES = [('documents1', 'documents1')]

class CustomForms(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        path = cleaned_data.get('path_BB')
        new_dir = cleaned_data.get('new_directory')
        
        # Se o usuário informou um novo diretório, cria o caminho completo
        if new_dir:
            # Escolhe o primeiro diretório base como pai do novo diretório
            parent_dir = self.BASE_DIRS[0] if self.BASE_DIRS else settings.MEDIA_ROOT
            
            # Cria o caminho completo
            new_path = os.path.join(parent_dir, new_dir)
            
            # Verifica se o diretorio ja existe
            if not os.path.exists(new_path):
                try:
                    os.makedirs(new_path)
                    # Retorna o caminho relativos para ser salvo
                    cleaned_data['path_BB'] = os.path.relpath(new_path, settings.MEDIA_ROOT)
                except OSError as e:
                    self.add_error('new_directory', f"Erro ao criar diretório: {str(e)}")
            else:
                cleaned_data['path_BB'] = os.path.relpath(new_path, settings.MEDIA_ROOT)
                
        return cleaned_data

class BBForms(CustomForms):
    arquivo_BB = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo_bb",
            }
        ),
    )
    
    # Campo opcional para criar um novo subdiretório
    new_directory = forms.CharField(
        label="Ou criar novo subdiretório",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control mt-2",
                "placeholder": "Nome do novo subdiretório (opcional)",
                "id": "new_directory",
            }
        ),
    )

class SICREDIForms(CustomForms):
    arquivo_SICREDI = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )

    # Campo opcional para criar um novo subdiretório
    new_directory = forms.CharField(
        label="Ou criar novo subdiretório",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control mt-2",
                "placeholder": "Nome do novo subdiretório (opcional)",
                "id": "new_directory",
            }
        ),
    )

class RecibosPagForms(CustomForms):
    arquivo_recibos_pag = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )

    # Campo opcional para criar um novo subdiretório
    new_directory = forms.CharField(
        label="Ou criar novo subdiretório",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control mt-2",
                "placeholder": "Nome do novo subdiretório (opcional)",
                "id": "new_directory",
            }
        ),
    )

class ImpostoRendaForms(CustomForms):
    arquivo_imposto_renda = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )

    # Campo opcional para criar um novo subdiretório
    new_directory = forms.CharField(
        label="Ou criar novo subdiretório",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control mt-2",
                "placeholder": "Nome do novo subdiretório (opcional)",
                "id": "new_directory",
            }
        ),
    )

class SomaPayForms(CustomForms):
    arquivo_somapay = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )

    # Campo opcional para criar um novo subdiretório
    new_directory = forms.CharField(
        label="Ou criar novo subdiretório",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control mt-2",
                "placeholder": "Nome do novo subdiretório (opcional)",
                "id": "new_directory",
            }
        ),
    )