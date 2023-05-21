from __future__ import annotations

import os
from typing import Any, Optional
from discord.ext import commands, menus
from discord import app_commands
import discord
from .utils.paginator import RoboPages
import logging
import re
from .utils.context import Context
GUILD = int(os.getenv("GUILD"))


log = logging.getLogger(__name__)


class UrbanDictionaryPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r'(\[(.+?)\])')

    def __init__(self, data: list[dict[str, Any]]):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition: str, *, regex=BRACKETED) -> str:
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + ' [...]'
        return ret

    async def format_page(self, menu: RoboPages, entry: dict[str, Any]):
        maximum = self.get_max_pages()
        title = f'{entry["word"]}: {menu.current_page + 1} out of {maximum}' if maximum else entry['word']
        embed = discord.Embed(title=title, colour=0xE86222,
                              url=entry['permalink'])
        embed.set_footer(text=f'by {entry["author"]}')
        embed.description = self.cleanup_definition(entry['definition'])

        try:
            up, down = entry['thumbs_up'], entry['thumbs_down']
        except KeyError:
            pass
        else:
            embed.add_field(
                name='Votes', value=f'\N{THUMBS UP SIGN} {up} \N{THUMBS DOWN SIGN} {down}', inline=False)

        try:
            date = discord.utils.parse_time(entry['written_on'][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed


class FeedbackModal(discord.ui.Modal, title='Submit Feedback'):
    summary = discord.ui.TextInput(
        label='Summary', placeholder='A brief explanation of what you want')
    details = discord.ui.TextInput(
        label='Details', style=discord.TextStyle.long, required=False)

    def __init__(self, cog) -> None:
        super().__init__()
        self.cog: Service = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        channel = self.cog.feedback_channel
        if channel is None:
            await interaction.response.send_message('Could not submit your feedback, sorry about this', ephemeral=True)
            return

        embed = self.cog.get_feedback_embed(
            interaction, summary=str(self.summary), details=self.details.value)
        await channel.send(embed=embed)
        await interaction.response.send_message('Successfully submitted feedback', ephemeral=True)


class Service(commands.Cog):
    """Service commands"""

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self) -> None:
        self._spoiler_view.stop()

    @property
    def feedback_channel(self) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(GUILD)

        if guild is None:
            return None

        return guild.system_channel  # type: ignore

    def get_feedback_embed(
        self,
        obj: Context | discord.Interaction,
        *,
        summary: str,
        details: Optional[str] = None,
    ) -> discord.Embed:
        e = discord.Embed(title='Feedback', colour=0x738BD7)

        if details is not None:
            e.description = details
            e.title = summary[:256]
        else:
            e.description = summary

        if obj.guild is not None:
            e.add_field(
                name='Server', value=f'{obj.guild.name} (ID: {obj.guild.id})', inline=False)

        if obj.channel is not None:
            e.add_field(
                name='Channel', value=f'{obj.channel} (ID: {obj.channel.id})', inline=False)

        if isinstance(obj, discord.Interaction):
            e.timestamp = obj.created_at
            user = obj.user
        else:
            e.timestamp = obj.message.created_at
            user = obj.author

        e.set_author(name=str(user), icon_url=user.display_avatar.url)
        e.set_footer(text=f'Author ID: {user.id}')
        return e

    @commands.command()
    @commands.cooldown(rate=1, per=60.0, type=commands.BucketType.user)
    async def feedback(self, ctx: Context, *, content: str):
        """Gives feedback about the bot.

        This is a quick way to request features or bug fixes
        without being in the bot's server.

        The bot will communicate with you via PM about the status
        of your request if possible.

        You can only request feedback once a minute.
        """

        channel = self.feedback_channel
        if channel is None:
            return

        e = self.get_feedback_embed(ctx, summary=content)
        await channel.send(embed=e)
        await ctx.send(f'{ctx.tick(True)} Successfully sent feedback')

    @app_commands.command(name='feedback')
    async def feedback_slash(self, interaction: discord.Interaction):
        """Give feedback about the bot directly to the owner."""
        await interaction.response.send_modal(FeedbackModal(self))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def pm(self, ctx: Context, user_id: int, *, content: str):
        user = self.bot.get_user(user_id) or (await self.bot.fetch_user(user_id))

        fmt = (
            content + '\n\n*This is a DM sent because you had previously requested feedback or I found a bug'
            ' in a command you used, I do not monitor this DM.*'
        )
        try:
            await user.send(fmt)
        except:
            await ctx.send(f'Could not PM user by ID {user_id}.')
        else:
            await ctx.send('PM successfully sent.')

    @commands.command(name='urban')
    async def _urban(self, ctx: Context, *, word: str):
        """Searches urban dictionary."""

        url = 'http://api.urbandictionary.com/v0/define'
        async with ctx.session.get(url, params={'term': word}) as resp:
            if resp.status != 200:
                return await ctx.send(f'An error occurred: {resp.status} {resp.reason}')

            js = await resp.json()
            data = js.get('list', [])
            if not data:
                return await ctx.send('No results found, sorry.')

        pages = RoboPages(UrbanDictionaryPageSource(data), ctx=ctx)
        await pages.start()


async def setup(bot):
    await bot.add_cog(Service(bot))
