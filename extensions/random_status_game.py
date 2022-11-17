import discord
import random
import asyncio
from discord.ext import commands
GAMES = [
    'Battlefield 3',
    'Battlefield 4',
    'Minecraft',
    'Apex Legends',
    'Rocket League',
    'Doom 2',
    'Half Life',
    'Hell Let Loose',
    'Battlefield 1',
    'Pornhub',
    'New World',
    'TV',
    'Onlyfans',
    'with your mom\'s tits',
    'with poops',
    'dicks'
]


class RandomStatusGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._running = False

    async def set_status(self, title):
        await self.bot.change_presence(activity=discord.Game(name=title, type=1))

    @commands.Cog.listener()
    async def on_ready(self):
        if self._running:
            return

        self._running = True
        try:
            while not self.bot.is_closed():
                name = random.choice(GAMES)
                await self.bot.change_presence(activity=discord.Game(name=name, type=1))
                await asyncio.sleep(300)
        finally:
            self._running = False

async def setup(bot):
    await bot.add_cog(RandomStatusGame(bot))