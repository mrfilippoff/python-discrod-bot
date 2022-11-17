import discord
import random
import asyncio
from discord.ext import commands
GAMES = [
    'Call of Duty: Modern Warfare',
    'Battlefield 3',
    'Battlefield 4',
    'Minecraft',
    'Apex Legends',
    'Rocket League',
    'Doom 2',
    'Half Life',
    'Hell Let Loose',
    'Battlefield 1',
    'Pornhub'
]


class RandomStatusGame(commands.Cog):
    # A simple plugin that will cycle based on a preset list of games
    # https: // github.com / CarlosFdez / SpueBox / blob / master / plugins / randomgame.py

    def __init__(self, client):
        self.client = client
        self._running = False

    async def set_status(self, title):
        await self.client.change_presence(activity=discord.Game(name=title, type=1))

    @commands.Cog.listener()
    async def on_ready(self):
        # on_ready could be called multiple times, so we try to only go at it once
        if self._running:
            return

        self._running = True
        try:
            while not self.client.is_closed():
                name = random.choice(GAMES)
                await self.client.change_presence(activity=discord.Game(name=name, type=1))
                await asyncio.sleep(300)
        finally:
            self._running = False


def setup(client):
    client.add_cog(RandomStatusGame(client))

