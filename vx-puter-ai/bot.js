import dotenv from 'dotenv';
dotenv.config();
import { Client, GatewayIntentBits } from 'discord.js';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

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
        '--disable-gpu'
      ],
      ignoreHTTPSErrors: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH
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
    
    // Capturar screenshot para diagnóstico solo si page existe
    try {
      if (page) {
        await page.screenshot({ path: 'error.png' });
        console.log('📸 Captura de pantalla guardada: error.png');
      } else {
        console.log('⚠️ No se pudo capturar pantalla: page no está definido');
      }
    } catch (screenshotErr) {
      console.error('Error al capturar pantalla:', screenshotErr);
    }
    
    // Cerrar el navegador si existe
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

client.on('messageCreate', async (message) => {
  if (message.author.bot || !page) return;

  const userId = message.author.id;
  const content = message.content.trim();

  // !ai prompt
  if (content.startsWith('!ai ')) {
    const prompt = content.slice(4);
    const modelo = userModels[userId] || MODELOS.claude;

    try {
      await message.channel.sendTyping();

      const respuesta = await page.evaluate(async (prompt, modelo) => {
        const resp = await window.puter.ai.chat(prompt, {
          model: modelo,
          temperature: 0.7
        });
        return resp.message.content;
      }, prompt, modelo);

      if (respuesta.length > 2000) {
        const partes = respuesta.match(/.{1,1900}/g) || [];
        for (let i = 0; i < partes.length && i < 3; i++) {
          await message.reply(partes[i]);
        }
        if (partes.length > 3) await message.reply('... (respuesta truncada)');
      } else {
        await message.reply(respuesta);
      }

    } catch (err) {
      console.error('❌ Error en !ai:', err);
      await message.reply('⚠️ Ocurrió un error al procesar la respuesta.');
    }
  }

  // !setmodel modelo
  if (content.startsWith('!setmodel ')) {
    const modelo = content.slice(10).trim().toLowerCase();
    if (MODELOS[modelo]) {
      userModels[userId] = MODELOS[modelo];
      message.reply(`✅ Modelo cambiado a **${modelo}**`);
    } else {
      message.reply(`❌ Modelo no válido. Usa: ${Object.keys(MODELOS).join(', ')}`);
    }
  }

  // !mymodel
  if (content === '!mymodel') {
    const actual = userModels[userId] || MODELOS.claude;
    const nombre = Object.keys(MODELOS).find(k => MODELOS[k] === actual);
    message.reply(`🤖 Tu modelo actual: **${nombre}**`);
  }

  // !models
  if (content === '!models') {
    const lista = Object.entries(MODELOS)
      .map(([k, v]) => `• **${k}** → ${v.split('/').pop()}`).join('\n');
    message.reply(`📚 Modelos disponibles:\n${lista}`);
  }

  // !help
  if (content === '!help') {
    const ayuda = `
🤖 **Comandos disponibles:**

\`!ai [prompt]\` — Envia una pregunta o idea
\`!setmodel [modelo]\` — Cambia el modelo de IA
\`!mymodel\` — Muestra tu modelo actual
\`!models\` — Lista de modelos disponibles
\`!help\` — Muestra este menú de ayuda
    `;
    message.reply(ayuda);
  }
});

client.login(process.env.DISCORD_TOKEN);
