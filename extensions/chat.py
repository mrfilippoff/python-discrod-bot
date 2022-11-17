import random
import datetime
import asyncio
from discord.ext import commands
import chat
from discord import MessageType


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = chat.ChatBot()

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or message.type is not MessageType.default or len(message.attachments) > 0:
            return

        to_everyone_random = random.random() + random.random() > 1.5 and datetime.datetime.today().second % 2

        if self.bot.user.mentioned_in(message):
            await self.reply(message)
        else:
            if (to_everyone_random):
                await self.reply(message)


    async def reply(self, message):
        print('send')
        async with message.channel.typing():
            text = self.chatbot.get_reply(message.clean_content)
            await message.channel.send(text)


async def setup(bot):
    await bot.add_cog(Chat(bot))