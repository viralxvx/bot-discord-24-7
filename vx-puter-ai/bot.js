require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const puppeteer = require('puppeteer');

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
  browser = await puppeteer.launch({ headless: true });
  page = await browser.newPage();
  await page.goto('https://puter.com/', { waitUntil: 'domcontentloaded' });
  await page.addScriptTag({ url: 'https://js.puter.com/v2/' });

  // Confirmar que Puter.js está cargado
  await page.waitForFunction(() => window.puter !== undefined);
  console.log('✅ Puter.js cargado correctamente en Puppeteer');
}

client.once('ready', async () => {
  console.log(`🤖 Bot conectado como ${client.user.tag}`);
  await iniciarPuter();
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
        const partes = respuesta.match(/.{1,1900}/g);
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
