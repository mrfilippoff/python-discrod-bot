from dotenv import load_dotenv
import os
from discord import Intents
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("TOKEN")
EXTENSION_DIR = os.getenv("EXTENSIONS_DIR")

intents = Intents.all()
intents.presences = True
intents.guilds = True
intents.members = True
intents.emojis = True
intents.guild_messages = True
intents.reactions = True
intents.voice_states = True
intents.messages = True
intents.message_content = True


class TeaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='+', intents=intents)

    async def setup_hook(self):
        for filename in os.listdir(f'./{EXTENSION_DIR}'):
            if filename.endswith('.py'):
                await self.load_extension(f'{EXTENSION_DIR}.{filename[:-3]}')

bot = TeaBot()
bot.run(TOKEN)