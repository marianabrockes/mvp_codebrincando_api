# Imagem base do Python
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia as dependências primeiro (ajuda no cache)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da API, incluindo app.py e database.db
COPY . .

# Deixa logs sem buffer (saiem na hora no docker logs)
ENV PYTHONUNBUFFERED=1

# Expõe a porta da API dentro do container
EXPOSE 5001

# Comando para iniciar a API
CMD ["python", "app.py"]