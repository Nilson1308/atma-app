# Usamos uma imagem oficial do Python como base
FROM python:3.10-slim-buster

# Define variáveis de ambiente
# Evita que o Python gere arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que o output do Python seja enviado diretamente para o terminal
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências para o diretório de trabalho
COPY requirements.txt /app/

# Instala as dependências do projeto
# --no-cache-dir desabilita o cache para manter a imagem menor
# psycopg2-binary é o driver para conectar com o PostgreSQL
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo da pasta 'backend' local para o diretório de trabalho no contêiner
COPY . /app/
