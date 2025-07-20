import dotenv from 'dotenv';
dotenv.config();
import { Client, GatewayIntentBits } from 'discord.js';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

let browser, page;

const MODELOS = {
  claude: 'openrouter:anthropic/claude-sonnet-4',
  gpt4: 'openrouter:openai/gpt-4o',
  llama: 'openrouter:meta-llama/llama-3.1-8b-instruct',
  gemini: 'openrouter:google/gemini-2.5-flash',
  mistral: 'openrouter:mistralai/mistral-7b-instruct'
};

let userModels = {};

async function iniciarPuter() {
  try {
    console.log('🚀 Iniciando Puppeteer...');
    
    browser = await puppeteer.launch({
      headless: 'new',
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
      ignoreHTTPSErrors: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || null
    });

    page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36');
    
    console.log('🌐 Navegando a puter.com...');
    await page.goto('https://puter.com/', {
      waitUntil: 'networkidle2',
      timeout: 60000
    });

    console.log('⬆️ Inyectando Puter.js...');
    await page.addScriptTag({ url: 'https://js.puter.com/v2/' });
    
    await page.waitForFunction(() => typeof window.puter !== 'undefined', {
      timeout: 30000,
      polling: 500
    });
    
    const puterLoaded = await page.evaluate(() => {
      return typeof window.puter === 'object' && 
             typeof window.puter.ai === 'object' &&
             typeof window.puter.ai.chat === 'function';
    });
    
    if (!puterLoaded) throw new Error('Puter.js no se inicializó correctamente');
    
    console.log('✅ Puter.js cargado correctamente');
    return true;
    
  } catch (err) {
    console.error('❌ Error crítico en iniciarPuter:', err);
    
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
  
  let attempts = 0;
  while (attempts < 3) {
    attempts++;
    console.log(`🔄 Intento ${attempts}/3 de iniciar Puter.js`);
    
    if (await iniciarPuter()) break;
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  
  if (attempts >= 3) {
    console.error('⚠️ Puter.js no pudo iniciarse después de 3 intentos');
  }
});

client.on('messageCreate', async (message) => {
  // ... (mantén igual el resto del handler de mensajes)
  // Solo cambia los requires por imports arriba
});

client.login(process.env.DISCORD_TOKEN);
