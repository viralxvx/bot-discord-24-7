# Usar imagen oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y luego instalar
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# Puerto que expone el bot (en caso de webserver, opcional)
EXPOSE 8080

# Comando para iniciar el bot
CMD ["python", "main.py"]
