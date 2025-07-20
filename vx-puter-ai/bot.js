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
        '--js-flags="--max-old-space-size=2048"'
      ],
      ignoreHTTPSErrors: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH
    });

    page = await browser.newPage();
    
    // Configurar User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36');
    
    // Configurar tiempo de espera
    page.setDefaultTimeout(30000);
    
    console.log('🌐 Navegando a puter.com...');
    await page.goto('https://puter.com/', {
      waitUntil: 'networkidle2',
      timeout: 60000
    });

    // Inyectar Puter.js
    console.log('⬆️ Inyectando Puter.js...');
    await page.addScriptTag({ url: 'https://js.puter.com/v2/' });
    
    // Esperar a que Puter.js cargue con verificación mejorada
    await page.waitForFunction(() => {
      try {
        return typeof window.puter !== 'undefined' && 
               typeof window.puter.ai !== 'undefined' &&
               typeof window.puter.ai.chat === 'function';
      } catch (e) {
        return false;
      }
    }, {
      timeout: 60000,
      polling: 1000
    });
    
    console.log('✅ Puter.js cargado correctamente');
    return true;
    
  } catch (err) {
    console.error('❌ Error crítico en iniciarPuter:', err);
    
    try {
      if (page) {
        await page.screenshot({ path: 'error.png' });
        console.log('📸 Captura de pantalla guardada: error.png');
      }
    } catch (screenshotErr) {
      console.error('Error al capturar pantalla:', screenshotErr);
    }
    
    if (browser) await browser.close();
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
  
  if (attempts >= 3) {
    console.error('⚠️ Puter.js no pudo iniciarse después de 3 intentos');
  }
});

client.on('messageCreate', async (message) => {
  // Ignorar mensajes de bots y si no tenemos página activa
  if (message.author.bot || !page) return;
  
  // Verificar si estamos en el canal correcto
  const enCanalAI = canalAI && message.channel.id === canalAI;
  
  // Solo responder en el canal designado
  if (!enCanalAI) return;
  
  const userId = message.author.id;
  let prompt = message.content.trim();
  
  // Sistema para cambiar modelo mediante mención especial
  const cambioModelo = prompt.match(/modelo:(\w+)/i);
  if (cambioModelo) {
    const modeloKey = cambioModelo[1].toLowerCase();
    if (MODELOS[modeloKey]) {
      userModels[userId] = MODELOS[modeloKey];
      await message.reply(`✅ Modelo cambiado a **${modeloKey}**`);
      prompt = prompt.replace(cambioModelo[0], '').trim();
      
      // Si solo contenía el comando, no procesar IA
      if (!prompt) return;
    } else {
      const modelosDisponibles = Object.keys(MODELOS).join(', ');
      await message.reply(`❌ Modelo no válido. Usa: ${modelosDisponibles}\nEjemplo: "modelo:gpt4"`);
      return;
    }
  }
  
  // Obtener modelo del usuario o usar el predeterminado
  const modelo = userModels[userId] || MODELOS.claude;
  
  try {
    // Indicar que está escribiendo
    await message.channel.sendTyping();
    
    console.log(`Procesando prompt: "${prompt}" con modelo: ${modelo}`);
    
    // Función de evaluación más robusta
    const respuesta = await page.evaluate(async (prompt, modelo) => {
      try {
        // Verificar que Puter.js sigue disponible
        if (typeof window.puter === 'undefined') {
          throw new Error('Puter.js no está disponible');
        }
        
        const resp = await window.puter.ai.chat(prompt, {
          model: modelo,
          temperature: 0.7,
          max_tokens: 1000
        });
        
        return resp.message.content;
      } catch (e) {
        // Capturar error en el contexto del navegador
        return `ERROR: ${e.message}`;
      }
    }, prompt, modelo);
    
    // Manejar errores de Puter.js
    if (respuesta.startsWith('ERROR:')) {
      throw new Error(respuesta);
    }
    
    console.log(`Respuesta recibida (${respuesta.length} caracteres)`);
    
    // Manejar respuestas largas
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
    console.error('❌ Error en IA:', err.message);
    
    // Mensaje de error más específico
    let errorMsg = '⚠️ Ocurrió un error al procesar tu mensaje.';
    
    if (err.message.includes('Puter.js no está disponible')) {
      errorMsg += '\n🔁 Intentando reiniciar Puter.js...';
      await iniciarPuter();
    }
    else if (err.message.includes('timeout')) {
      errorMsg = '⏱️ La respuesta tardó demasiado. Intenta con un prompt más corto.';
    }
    
    await message.reply(errorMsg);
  }
});

client.login(process.env.DISCORD_TOKEN);
