from django import forms
from django.conf import settings
from django.forms import Form

from django import forms
from django.utils.safestring import mark_safe

class DirectoryPathWidget(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs)
        script = """
        <script>
            function selectFolder(inputId) {
                var input = document.createElement('input');
                input.type = 'file';
                input.webkitdirectory = true;  // Permite escolher diretórios
                input.directory = true;
                input.style.display = 'none';

                input.addEventListener('change', function() {
                    var folderPath = input.files[0].webkitRelativePath.split('/')[0];  
                    document.getElementById(inputId).value = folderPath;
                });

                document.body.appendChild(input);
                input.click();
                document.body.removeChild(input);
            }
        </script>
        """
        button_html = f'<button type="button" onclick="selectFolder(\'id_{name}\')">Selecionar Pasta</button>'
        return mark_safe(f"{input_html}{button_html}{script}")



class DirectoryPathField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = DirectoryPathWidget()
        super().__init__(*args, **kwargs)



class BBForms(Form):
    arquivo_BB = forms.FileField(
        label="Arquivo",
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o arquivo",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        ),
    )

    path_BB = forms.CharField(
        label="path",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o caminho para salvar os arquivos",
                "id": "arquivo",
            }
        ),
    )

class SICREDIForms(Form):
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

    path_SICREDI = forms.CharField(
        label="path",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o caminho para salvar os arquivos",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )

class RecibosPagForms(Form):
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

    pasta = DirectoryPathField(label="Selecione a pasta")

    path_recibos_pag = forms.CharField(
        label="path",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border form-control",
                "placeholder": "Selecione o caminho para salvar os arquivos",
                "id": "arquivo",  # Ajuste o ID para corresponder ao campo
            }
        )
    )