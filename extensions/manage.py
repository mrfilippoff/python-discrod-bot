import asyncio
import os
import requests
from discord.ext import commands
from discord import (Member, MessageType, Object, File)

from collections import Counter
from .utils.misc import guild_send, random_reactions, guild_send_image
from .utils.context import GuildContext


RECYCLED_LIMIT = 5
RECYCLED_EMOJI = '♻️'
RECYCLED_TIME_LIMIT = 60

NO_PENIS_EMOJI = ':No_Penis_TeaServer:'
NO_PENIS_LIMIT = 1
NO_PENIS_TIME_LIMIT = 3
#NO_PENIS_GUILD = Object(id=1342131380032639017)
#NO_PENIS_CHANNEL_ID = 342131380032639017
NO_PENIS_CHANNEL_ID=797937369651216414

DEFAULT_GREET = 'pick a role for your game to see voice/text channels'
GUILD = Object(id=os.getenv("GUILD") or 0)

EXCLUDE_ENOJIS_LIST = [RECYCLED_EMOJI, '🤖']

def is_no_penis_emoji(emoji: str):
    return 'No_Penis_TeaServer' in emoji


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot started')
        self.bot.tree.copy_global_to(guild=GUILD)
        await self.bot.tree.sync(guild=GUILD)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        await guild_send(
            member.guild,
            content=f'Ladies and gentlemen! **{member.display_name}** has left the server!'
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        try:
            channel_id = int(self.bot.options.get(
                "greet_channel", 0))
            greet_text = self.bot.options.get("greet_text", DEFAULT_GREET)
            channel = self.bot.get_channel(channel_id)

            await channel.send(
                f'{member.mention} {greet_text}',
                delete_after=int(self.bot.options.get(
                    "greet_text_delay") or 10)
            )

        except Exception:
            pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, _: Member):
        print('OK?', is_no_penis_emoji(reaction.emoji.name))
        if  len(reaction.message.attachments) > 0:
            print(reaction.message.attachments, reaction.emoji)

        if reaction.emoji not in EXCLUDE_ENOJIS_LIST and not is_no_penis_emoji(reaction.emoji.name):
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

        if is_no_penis_emoji(reaction.emoji.name) and reaction.count == NO_PENIS_LIMIT and len(reaction.message.attachments) > 0:
            alert = await reaction.message.reply(f'Hey {reaction.message.author.mention}! {NO_PENIS_LIMIT} people are sure that you posted a dick.. oops i mean "penis"')
            await asyncio.sleep(NO_PENIS_TIME_LIMIT)

            try:
                guild = reaction.message.author.guild
                await alert.delete()
                files_a = [await attachment.to_file(filename=attachment.filename) for attachment in reaction.message.attachments]
                need_jesus_chan = self.bot.get_channel(NO_PENIS_CHANNEL_ID)
                await need_jesus_chan.send('here we go', files=files_a)

                await reaction.message.delete()

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
        is_author_admin = ctx.channel.permissions_for(
            ctx.author).manage_messages

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
        messages = [
            f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']

        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(),
                              key=lambda t: t[1], reverse=True)
            messages.extend(
                f'- **{author}**: {count}' for author, count in spammers)

        await ctx.send('\n'.join(messages))


async def setup(bot):
    await bot.add_cog(Manage(bot))
