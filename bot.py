from dotenv import load_dotenv
import aiohttp
import os
from discord import Intents
from discord.ext import commands, tasks

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


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='+', intents=intents)


    async def setup_hook(self):
        # self.background_task.start()
        self.session = aiohttp.ClientSession()

        for filename in os.listdir(f'./{EXTENSION_DIR}'):
            if filename.endswith('.py'):
                await self.load_extension(f'{EXTENSION_DIR}.{filename[:-3]}')


    async def close(self):
        await super().close()
        await self.session.close()

    # @tasks.loop(minutes=10)
    # async def background_task(self):
    #     print('Running background task...')

bot = MyBot()
bot.run(TOKEN)