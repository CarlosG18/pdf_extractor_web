# Usa a imagem oficial do Python
FROM python:3.12

# Define um usuário não root
RUN useradd -m appuser

# Instala pacotes necessários
RUN apt-get update && apt-get install -y \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Cria um ambiente virtual e instala dependências
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/midia && chown -R appuser:appuser /app/midia

# Define a variável de ambiente para o ambiente virtual
ENV PATH="/app/venv/bin:$PATH"

# Expõe a porta 8000
EXPOSE 8000

# Define o usuário não root para rodar o contêiner
USER appuser

# Define o comando de inicialização
ENTRYPOINT ["python"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]
