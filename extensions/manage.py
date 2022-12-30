import asyncio
import logging
import db
import os
from typing import List
import random
from discord.ext import commands

from discord import MessageType, Object
from utils import  guild_send, random_reactions
from ui import RolesView

RECYCLED_LIMIT = 3
RECYCLED_EMOJI = '♻️'

#TEA_GUILD = 434382331835318278  # real
TEA_GUILD = 574605836308054027 #testeacles

EVERYONE = '@everyone'
GUILD = Object(id= os.getenv("GUILD") or 0)

class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot started')
        self.bot.tree.copy_global_to(guild=GUILD)
        await self.bot.tree.sync(guild=GUILD)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await guild_send(member.guild, content=f'Ladies and gentlemen! **{member.display_name}** has left the server!')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji != RECYCLED_EMOJI and reaction.emoji != '🤖':
            await reaction.message.add_reaction(reaction.emoji)

        if reaction.emoji == RECYCLED_EMOJI and reaction.count == RECYCLED_LIMIT and len(reaction.message.attachments) > 0:
            alert = await reaction.message.reply(f'Hey {reaction.message.author.mention}! {RECYCLED_LIMIT} people saying you posted an old blah content, if you feel ashamed to delete it, let me do it?')
            await asyncio.sleep(60)

            try:
                await alert.delete()
                await reaction.message.delete()
                await guild_send(reaction.message.author.guild, content=f'Ladies and gentlemen! **{reaction.message.author.display_name}** has posted a bit of an old shit and i have already removed it. God bless me! ✝️')
            except Exception as e:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        random_int = random.choice(range(0, 10))

        if message.author.premium_since and random_int == 1:
            return await random_reactions(message, 2, 30)

        elif message.type == MessageType.new_member:
            return await random_reactions(message, 1)

        elif message.type == MessageType.premium_guild_subscription:
            return await random_reactions(message)
        else:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        message = f'Holy shit: **{user.name}**\'s gone! Damn'
        return await guild_send(guild, content=message)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        message = f'Oh! Look this: **{user.name}** was forgiven by the gods and he can come back to us!' \
                    f'Prepare your cocks!'
        return await guild_send(guild, content=message)


    @commands.hybrid_command(name='my_roles', with_app_command=True)
    async def my_roles(self, ctx):
        view = RolesView(ctx.guild.roles, ctx.message.author)
        view.message = await ctx.send('Update your game roles', view=view, ephemeral=True)


    @commands.hybrid_command(name='purge_channel', with_app_command=True)
    @commands.has_permissions(manage_guild=True)
    async def purge_channel(self, ctx, limit):
        try:
            deleted = await ctx.channel.purge(limit=int(limit))
            await ctx.channel.send('Deleted {} message(s) :yum:'.format(len(deleted)), delete_after=15)
        except Exception as e:
            await ctx.channel.reply(f'Oops. Error. {e}')


async def setup(bot):
    await bot.add_cog(Manage(bot))