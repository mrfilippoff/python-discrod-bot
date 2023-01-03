import random
import re
import datetime
from discord.ext import commands
import chat
from discord import MessageType
from utils import random_reactions
from ui import STFUView
from global_vars import STFU_USERS

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = chat.ChatBot()

    @commands.Cog.listener()
    async def on_message(self, message):

        if str(message.author.id) in STFU_USERS:
            async with message.channel.typing():
                shut_text = random.choice(['Hey! Shut the fuck up', 'STFU', 'Shut up, ok?', 'Shut your mouth right now'])
                await message.reply(shut_text)
                return

        if message.author.bot or message.type is not MessageType.default or len(message.attachments) > 0:
            return

        to_everyone_random = random.random() + random.random() > 1.55 and datetime.datetime.today().second % 2

        if self.bot.user.mentioned_in(message):
            await self.reply(message, True)
        else:
            if (to_everyone_random):
                await self.reply(message)


    async def reply(self, message, mention=False):
        prepare_message = re.sub('@.*? ', '', message.clean_content) or None

        if not prepare_message:
            return

        async with message.channel.typing():
            text = self.chatbot.get_reply(prepare_message) or random.choice(['no comments', 'what an idiot!', 'lol'])

            if mention:
                if random.random() + random.random() > 1.2: 
                    await random_reactions(message, 1, 5)

                await message.channel.send(f'{message.author.mention} {text}')
                return
            await message.channel.send(text)

    @commands.has_permissions(manage_guild=True)
    @commands.hybrid_command(name='stfu', with_app_command=True)
    async def stfu(self, ctx):
        """Ask someone to shut up"""
        view = STFUView()
        view.message = await ctx.send('Select user again to delete him from STFU list', view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Chat(bot))