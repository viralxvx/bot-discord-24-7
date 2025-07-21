import dotenv from 'dotenv';
dotenv.config();
import { Client, GatewayIntentBits } from 'discord.js';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import express from 'express';
import fs from 'fs';

// Health check endpoint
const app = express();
const PORT = process.env.PORT || 3000;
app.get('/health', (req, res) => res.status(200).send('OK'));
app.listen(PORT, () => console.log(`🩺 Health check running on port ${PORT}`));

// Configuración stealth para Puppeteer
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
const canalAI = process.env.VX_AI_CANAL;

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
        '--single-process',
        '--js-flags="--max-old-space-size=512"',
        '--memory-pressure-off'
      ],
      ignoreHTTPSErrors: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH
    });

    page = await browser.newPage();
    
    // Configurar User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36');
    
    // Configurar tiempo de espera
    page.setDefaultTimeout(20000);
    
    console.log('🌐 Navegando a puter.com...');
    await page.goto('https://puter.com/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });

    // Inyectar Puter.js
    console.log('⬆️ Inyectando Puter.js...');
    await page.addScriptTag({ url: 'https://js.puter.com/v2/' });
    
    // Esperar a que Puter.js cargue
    await page.waitForFunction(() => {
      try {
        return typeof window.puter !== 'undefined' && 
               typeof window.puter.ai !== 'undefined' &&
               typeof window.puter.ai.chat === 'function';
      } catch (e) {
        return false;
      }
    }, {
      timeout: 30000,
      polling: 1000
    });
    
    console.log('✅ Puter.js cargado correctamente');
    return true;
    
  } catch (err) {
    console.error('❌ Error crítico en iniciarPuter:', err);
    return false;
  }
}

client.once('ready', async () => {
  console.log(`🤖 Bot conectado como ${client.user.tag}`);
  console.log(`📌 Canal de IA configurado: ${canalAI ? '#' + canalAI : 'NO CONFIGURADO'}`);
  
  // Intentar iniciar Puter.js
  let attempts = 0;
  while (attempts < 3) {
    attempts++;
    console.log(`🔄 Intento ${attempts}/3 de iniciar Puter.js`);
    
    if (await iniciarPuter()) break;
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
});

client.on('messageCreate', async (message) => {
  if (message.author.bot || !page) return;
  
  // Verificar canal
  const enCanalAI = canalAI && message.channel.id === canalAI;
  if (!enCanalAI) return;
  
  const userId = message.author.id;
  let prompt = message.content.trim();
  
  // Cambiar modelo
  const cambioModelo = prompt.match(/modelo:(\w+)/i);
  if (cambioModelo) {
    const modeloKey = cambioModelo[1].toLowerCase();
    if (MODELOS[modeloKey]) {
      userModels[userId] = MODELOS[modeloKey];
      await message.reply(`✅ Modelo cambiado a **${modeloKey}**`);
      prompt = prompt.replace(cambioModelo[0], '').trim();
      if (!prompt) return;
    } else {
      await message.reply(`❌ Modelo no válido. Usa: ${Object.keys(MODELOS).join(', ')}`);
      return;
    }
  }
  
  const modelo = userModels[userId] || MODELOS.claude;
  
  try {
    await message.channel.sendTyping();
    
    console.log(`Procesando prompt: "${prompt.substring(0, 50)}..."`);
    
    // Función de evaluación optimizada
    const respuesta = await page.evaluate(async (prompt, modelo) => {
      try {
        const resp = await window.puter.ai.chat(prompt, {
          model: modelo,
          temperature: 0.7,
          max_tokens: 800
        });
        return resp.message.content;
      } catch (e) {
        return `ERROR: ${e.message}`;
      }
    }, prompt, modelo);
    
    if (respuesta.startsWith('ERROR:')) {
      throw new Error(respuesta);
    }
    
    console.log(`Respuesta recibida (${respuesta.length} chars)`);
    
    // Manejar respuestas largas con archivo
    if (respuesta.length > 1500) {
      const fileName = `respuesta-${Date.now()}.txt`;
      fs.writeFileSync(fileName, respuesta);
      await message.reply({
        content: 'Respuesta demasiado larga. Aquí está el archivo:',
        files: [fileName]
      });
      fs.unlinkSync(fileName);
    } else {
      await message.reply(respuesta);
    }
    
  } catch (err) {
    console.error('❌ Error en IA:', err.message);
    await message.reply('⚠️ Ocurrió un error. Intenta de nuevo más tarde.');
  }
});

client.login(process.env.DISCORD_TOKEN);

// Manejar señal SIGTERM
process.on('SIGTERM', async () => {
  console.log('🛑 Recibida señal SIGTERM. Cerrando limpiamente...');
  
  try {
    if (browser) await browser.close();
    console.log('✅ Navegador cerrado');
  } catch (e) {
    console.error('Error cerrando navegador:', e);
  }
  
  process.exit(0);
});
