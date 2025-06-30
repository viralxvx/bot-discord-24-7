# Usar una imagen oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements para instalar dependencias primero (mejor cache)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código al contenedor
COPY . .

# Exponer puerto para servidor web (Flask)
EXPOSE 8080

# Comando para ejecutar el bot
CMD ["python", "main.py"]
