require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

// Configuración stealth para evitar bloqueos
puppeteer.use(StealthPlugin());

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

let browser, page;

// ... (el resto de tu código de modelos y handlers)

async function iniciarPuter() {
  try {
    console.log('🚀 Iniciando Puppeteer...');
    
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--single-process'
      ],
      ignoreHTTPSErrors: true
    });

    page = await browser.newPage();
    
    // Configurar User-Agent y encabezados
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36');
    
    console.log('🌐 Navegando a puter.com...');
    await page.goto('https://puter.com/', {
      waitUntil: 'networkidle2',
      timeout: 60000
    });

    // Inyectar Puter.js manualmente
    console.log('⬆️ Inyectando Puter.js...');
    await page.addScriptTag({ url: 'https://js.puter.com/v2/' });
    
    // Esperar con verificación redundante
    await page.waitForFunction(() => typeof window.puter !== 'undefined', {
      timeout: 30000,
      polling: 500
    });
    
    // Verificación adicional
    const puterLoaded = await page.evaluate(() => {
      return typeof window.puter === 'object' && 
             typeof window.puter.ai === 'object' &&
             typeof window.puter.ai.chat === 'function';
    });
    
    if (!puterLoaded) throw new Error('Puter.js no se inicializó correctamente');
    
    console.log('✅ Puter.js cargado correctamente en Puppeteer');
    return true;
    
  } catch (err) {
    console.error('❌ Error crítico en iniciarPuter:', err);
    
    // Capturar screenshot para diagnóstico
    try {
      await page.screenshot({ path: 'error.png' });
      console.log('📸 Captura de pantalla guardada: error.png');
    } catch (screenshotErr) {
      console.error('Error al capturar pantalla:', screenshotErr);
    }
    
    if (browser) await browser.close();
    return false;
  }
}

client.once('ready', async () => {
  console.log(`🤖 Bot conectado como ${client.user.tag}`);
  
  // Intentar hasta 3 veces con retry
  let attempts = 0;
  while (attempts < 3) {
    attempts++;
    console.log(`🔄 Intento ${attempts}/3 de iniciar Puter.js`);
    
    if (await iniciarPuter()) break;
    await new Promise(resolve => setTimeout(resolve, 10000)); // Espera 10 segundos
  }
  
  if (attempts >= 3) {
    console.error('⚠️ Puter.js no pudo iniciarse después de 3 intentos');
  }
});

// ... (el resto de tu código de handlers de mensajes)
