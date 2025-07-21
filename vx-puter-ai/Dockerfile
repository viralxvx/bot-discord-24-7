# Usa la imagen oficial de Node.js 18 en versión Slim
FROM node:18-bullseye-slim

# Instalar dependencias esenciales para Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxshmfence1 \
    xdg-utils \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Crear enlace simbólico para chromium
RUN ln -s /usr/bin/chromium /usr/bin/chromium-browser

# Configurar variables de entorno para Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV NODE_ENV=production

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero para aprovechar caché de Docker
COPY package*.json ./

# Instalar dependencias de producción
RUN npm install --production

# Copiar el resto de los archivos de la aplicación
COPY . .

# Exponer puerto para health checks
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["npm", "start"]
