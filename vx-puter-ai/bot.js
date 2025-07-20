require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const { JSDOM } = require('jsdom');
const fetch = require('node-fetch');

// 🧠 Configurar entorno de navegador simulado
const dom = new JSDOM(`<!DOCTYPE html><html><head></head><body></body></html>`, {
    url: 'https://localhost',
    pretendToBeVisual: true,
    resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.fetch = fetch;

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

// ☁️ Variable global para Puter
let puter = null;

// 🔄 Cargar Puter.js
async function loadPuter() {
    try {
        const script = dom.window.document.createElement('script');
        script.src = 'https://js.puter.com/v2/';
        script.onload = () => {
            puter = dom.window.puter;
            console.log('✅ Puter.js cargado');
        };
        dom.window.document.head.appendChild(script);

        await new Promise((resolve) => {
            const check = setInterval(() => {
                if (dom.window.puter) {
                    puter = dom.window.puter;
                    clearInterval(check);
                    resolve();
                }
            }, 100);
        });
    } catch (error) {
        console.error('❌ Error cargando Puter.js:', error);
    }
}

// 📌 Lista de modelos disponibles
const models = {
    'claude': 'openrouter:anthropic/claude-sonnet-4',
    'gpt4': 'openrouter:openai/gpt-4o',
    'llama': 'openrouter:meta-llama/llama-3.1-8b-instruct',
    'gemini': 'openrouter:google/gemini-2.5-flash',
    'mistral': 'openrouter:mistralai/mistral-7b-instruct'
};

let userModels = {};

client.once('ready', async () => {
    console.log(`🤖 Bot listo como ${client.user.tag}`);
    await loadPuter();
});

// 📥 Procesar mensajes
client.on('messageCreate', async (message) => {
    if (message.author.bot || !puter) return;

    const userId = message.author.id;

    // !ai [prompt]
    if (message.content.startsWith('!ai ')) {
        const prompt = message.content.slice(4);
        if (!prompt) return message.reply('❌ Escribe algo luego de `!ai`');

        try {
            await message.channel.sendTyping();
            const selectedModel = userModels[userId] || models.claude;
            const response = await puter.ai.chat(prompt, {
                model: selectedModel,
                temperature: 0.7
            });

            if (response.length > 2000) {
                const chunks = response.match(/.{1,1900}/g);
                for (let i = 0; i < chunks.length && i < 3; i++) {
                    await message.reply(chunks[i]);
                }
                if (chunks.length > 3) await message.reply('... (respuesta truncada)');
            } else {
                message.reply(response);
            }
        } catch (err) {
            console.error(err);
            message.reply('❌ Error: ' + err.message);
        }
    }

    // !setmodel [modelo]
    if (message.content.startsWith('!setmodel ')) {
        const modelName = message.content.slice(10).toLowerCase();
        if (models[modelName]) {
            userModels[userId] = models[modelName];
            message.reply(`✅ Cambiado a **${modelName}**`);
        } else {
            message.reply(`❌ Modelos disponibles: ${Object.keys(models).join(', ')}`);
        }
    }

    // !stream [prompt]
    if (message.content.startsWith('!stream ')) {
        const prompt = message.content.slice(8);
        if (!prompt) return message.reply('❌ Escribe algo luego de `!stream`');

        try {
            await message.channel.sendTyping();
            const selectedModel = userModels[userId] || models.claude;
            let responseText = '';
            const msg = await message.reply('🧠 Generando respuesta...');

            const response = await puter.ai.chat(prompt, {
                model: selectedModel,
                stream: true
            });

            for await (const part of response) {
                if (part?.text) {
                    responseText += part.text;
                    if (responseText.length % 50 === 0) {
                        const toShow = responseText.length > 2000 ? responseText.substring(0, 1997) + '...' : responseText;
                        await msg.edit(toShow);
                    }
                }
            }

            const finalText = responseText.length > 2000 ? responseText.substring(0, 1997) + '...' : responseText;
            await msg.edit(finalText);
        } catch (error) {
            console.error(error);
            message.reply('❌ Error en streaming: ' + error.message);
        }
    }

    // !models
    if (message.content === '!models') {
        const list = Object.keys(models)
            .map(key => `• **${key}** - ${models[key].split(':')[1]}`)
            .join('\n');
        message.reply(`🤖 **Modelos disponibles:**\n${list}`);
    }

    // !mymodel
    if (message.content === '!mymodel') {
        const model = userModels[userId] || models.claude;
        const name = Object.keys(models).find(key => models[key] === model) || 'claude';
        message.reply(`🔍 Tu modelo actual: **${name}**`);
    }

    // !help
    if (message.content === '!help') {
        const help = `
🤖 **Comandos disponibles:**

\`!ai [texto]\` – Preguntar a la IA  
\`!stream [texto]\` – Respuesta larga en vivo  
\`!setmodel [modelo]\` – Cambiar modelo de IA  
\`!mymodel\` – Ver tu modelo actual  
\`!models\` – Ver todos los modelos  
\`!help\` – Mostrar ayuda

**Modelos:** ${Object.keys(models).join(', ')}
        `;
        message.reply(help);
    }
});

client.on('error', console.error);
client.login(process.env.DISCORD_TOKEN);
