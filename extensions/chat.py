import random
import datetime
from discord.ext import commands
import chat

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chatbot = chat.ChatBot()

    @commands.Cog.listener()
    async def on_message(self, message):
        clean_message = message.clean_content
        to_everyone_random = random.random() + random.random() > 1.2 and datetime.datetime.today().second % 2

        if self.bot.user.mentioned_in(message):
            answer = self.chatbot.get_reply(clean_message)
            await message.channel.send(answer)

        else:
            if (to_everyone_random):
                answer = self.chatbot.get_reply(clean_message)
                await message.channel.send(answer)
            

async def setup(bot):
    await bot.add_cog(Chat(bot))