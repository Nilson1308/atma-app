# Usamos uma imagem oficial e mais recente do Python
FROM python:3.11-slim-bookworm

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala o pacote de gestão de idiomas e define o locale para pt_BR
RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

# Define as variáveis de ambiente para usar o idioma português
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR:pt
ENV LC_ALL pt_BR.UTF-8

# Define o diretório de trabalho
WORKDIR /app

# Copia e instala as dependências
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . /app/