import random
import re
import datetime
from discord.ext import commands
import chat
from discord import MessageType
from utils import random_reactions

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = chat.ChatBot()

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or message.type is not MessageType.default or len(message.attachments) > 0:
            return

        to_everyone_random = random.random() + random.random() > 1.6 and datetime.datetime.today().second % 2

        if self.bot.user.mentioned_in(message):
            await self.reply(message, True)
        else:
            if (to_everyone_random):
                await self.reply(message)


    async def reply(self, message, mention=False):
        prepare_message = re.sub('@.*? ', '', message.clean_content) 

        async with message.channel.typing():
            text = self.chatbot.get_reply(prepare_message)

            if mention:
                if random.random() + random.random() > 1.4: 
                    await random_reactions(message, 1, 5)

                await message.channel.send(f'{message.author.mention} {text}')
                return
            await message.channel.send(text)


async def setup(bot):
    await bot.add_cog(Chat(bot))