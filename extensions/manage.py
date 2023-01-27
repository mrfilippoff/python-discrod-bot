import asyncio
import os
from discord.ext import commands
from discord import MessageType, Object, Member
from collections import Counter
from .utils.misc import guild_send, random_reactions, guild_send_image
from .utils.context import GuildContext
from ui import RolesView


RECYCLED_LIMIT = 5
RECYCLED_TIME_LIMIT = 60
RECYCLED_EMOJI = '♻️'

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
            await asyncio.sleep(RECYCLED_TIME_LIMIT)

            try:
                guild = reaction.message.author.guild
                await alert.delete()
                await reaction.message.delete()
                await guild_send(guild, content=f'Ladies and gentlemen! **{reaction.message.author.display_name}** has posted a bit of an old shit and i have already removed it. God bless me! ✝️')
                await guild_send_image(guild, os.path.abspath('images/terminator-terminator-robot.gif'))
            except Exception as e:
                print(e)
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.type == MessageType.new_member:
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
        """Manage user roles"""
        view = RolesView(ctx.guild, ctx.message.author)
        view.message = await ctx.send('Update your game roles right now!', view=view, ephemeral=True)

    async def _basic_cleanup_strategy(self, ctx: GuildContext, search: int):
        count = 0

        async for msg in ctx.history(limit=search, before=ctx.message):
            if msg.author == ctx.me:
                await msg.delete()
                count += 1
        return {'Bot': count}

    async def _complex_cleanup_strategy(self, ctx: GuildContext, search: int):
        deleted = await ctx.channel.purge(limit=search, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    async def _regular_user_cleanup_strategy(self, ctx: GuildContext, search: int):

        def check(m):
            return m.author == ctx.me

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @commands.command()
    async def cleanup(self, ctx: GuildContext, search: int = 100):
        """Cleans up all messages from the channel.
        If a search number is specified, it searches that many messages to delete.
        After the cleanup is completed, the bot will send you a message with
        which people got their messages deleted and their count. This is useful
        to see which users are spammers.
        Members with Manage Messages can search up to 1000 messages.
        Members without can search up to 25 messages.
        """
        strategy = self._basic_cleanup_strategy
        is_author_admin = ctx.channel.permissions_for(ctx.author).manage_messages

        if ctx.channel.permissions_for(ctx.me).manage_messages:
            if is_author_admin:
                strategy = self._complex_cleanup_strategy
            else:
                strategy = self._regular_user_cleanup_strategy

        if is_author_admin:
            search = min(max(2, search), 1000)
        else:
            search = min(max(2, search), 25)

        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']

        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'- **{author}**: {count}' for author, count in spammers)

        await ctx.send('\n'.join(messages))

async def setup(bot):
    await bot.add_cog(Manage(bot))