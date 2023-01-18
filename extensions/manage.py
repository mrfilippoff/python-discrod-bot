import asyncio
import os
import random
from typing import Optional
from discord.ext import commands
from discord import MessageType, Object, Member, abc
from collections import Counter
from typing_extensions import Annotated
from .utils.misc import guild_send, random_reactions
from .utils import checks
from ui import RolesView
from .utils.context import GuildContext



RECYCLED_LIMIT = 3
RECYCLED_EMOJI = '♻️'

GUILD = Object(id= os.getenv("GUILD") or 0)

def can_execute_action(ctx: GuildContext, user: Member, target: Member) -> bool:
    return user.id == ctx.bot.owner_id or user == ctx.guild.owner or user.top_role > target.top_role

class ActionReason(commands.Converter):
    async def convert(self, ctx: GuildContext, argument: str):
        ret = f'{ctx.author} (ID: {ctx.author.id}): {argument}'

        if len(ret) > 512:
            reason_max = 512 - len(ret) + len(argument)
            raise commands.BadArgument(f'Reason is too long ({len(argument)}/{reason_max})')
        return ret


class MemberID(commands.Converter):
    async def convert(self, ctx: GuildContext, argument: str):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
            else:
                m = await ctx.bot.get_or_fetch_member(ctx.guild, member_id)
                if m is None:
                    # hackban case
                    return type('_Hackban', (), {'id': member_id, '__str__': lambda s: f'Member ID {s.id}'})()

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
        return m

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

    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: GuildContext,
        member: Annotated[abc.Snowflake, MemberID],
        *,
        reason: Annotated[Optional[str], ActionReason] = None,
    ):
        """Kicks a member from the server.
        To use this command you must have Kick Members permission.
        """
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await ctx.guild.kick(member, reason=reason)
        await ctx.send('\N{OK HAND SIGN}')

async def setup(bot):
    await bot.add_cog(Manage(bot))