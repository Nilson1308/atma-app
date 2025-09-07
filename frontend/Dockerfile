# Usamos uma imagem oficial do Node.js v20 como base (versão Alpine é menor)
FROM node:20-alpine

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# --- NOVA LÓGICA ---
# 1. Copia TUDO primeiro.
# Isso garante que quando o 'npm install' rodar, todos os arquivos de configuração do Quasar já estarão lá.
COPY . .

# 2. Instala as dependências do projeto.
# O script 'postinstall' agora vai encontrar o 'quasar.config.js' e funcionar.
RUN npm install

# 3. Instala o Quasar CLI globalmente (boa prática para ter o comando disponível)
RUN npm install -g @quasar/cli

# Expõe a porta 9000 para o servidor de desenvolvimento do Quasar
EXPOSE 9000
