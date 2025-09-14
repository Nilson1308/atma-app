# Usamos uma imagem oficial do Python como base
FROM python:3.10-slim-buster

# Define variáveis de ambiente
# Evita que o Python gere arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que o output do Python seja enviado diretamente para o terminal
ENV PYTHONUNBUFFERED 1

# Atualiza as fontes do apt para usar os arquivos do Debian para a versão "Buster"
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list

# Instala o pacote de gestão de idiomas e descomenta a linha do pt_BR
RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

# Define as variáveis de ambiente para usar o idioma português
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR:pt
ENV LC_ALL pt_BR.UTF-8

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
