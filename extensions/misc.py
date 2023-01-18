from __future__ import annotations
from typing_extensions import Annotated
from typing import Optional

from discord.ext import commands
import discord
import io

from .utils.translator import translate
from .utils.context import Context

# from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/funhouse.py
class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='cat', with_app_command=True)
    async def cat(self, ctx: Context):
        """Gives you a random cat."""
        async with ctx.session.get('https://api.thecatapi.com/v1/images/search') as resp:
            if resp.status != 200:
                return await ctx.send('No cat found :(')
            js = await resp.json()
            await ctx.send(embed=discord.Embed(title='Kitty').set_image(url=js[0]['url']))

    @commands.hybrid_command(name='dog', with_app_command=True)
    async def dog(self, ctx: Context):
        """Gives you a random dog."""
        async with ctx.session.get('https://random.dog/woof') as resp:
            if resp.status != 200:
                return await ctx.send('No dog found :(')

            filename = await resp.text()
            url = f'https://random.dog/{filename}'
            filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
            if filename.endswith(('.mp4', '.webm')):
                async with ctx.typing():
                    async with ctx.session.get(url) as other:
                        if other.status != 200:
                            return await ctx.send('Could not download dog video :(')

                        if int(other.headers['Content-Length']) >= filesize:
                            return await ctx.send(f'Video was too big to upload... See it here: {url} instead.')

                        fp = io.BytesIO(await other.read())
                        await ctx.send(file=discord.File(fp, filename=filename))
            else:
                await ctx.send(embed=discord.Embed(title='Doggo').set_image(url=url))

    @commands.hybrid_command(name='translate', with_app_command=True)
    async def translate(self, ctx: Context, *, message: Annotated[Optional[str], commands.clean_content] = None):
        """Translates a message to English using Google translate."""

        if message is None:
            reply = ctx.replied_message
            if reply is not None:
                message = reply.content
            else:
                return await ctx.send('Missing a message to translate')

        try:
            result = await translate(message, session=self.bot.session)
        except Exception as e:
            return await ctx.send(f'An error occurred: {e.__class__.__name__}: {e}')

        embed = discord.Embed(title='Translated', colour=0x4284F3)
        embed.add_field(name=f'From {result.source_language}', value=result.original, inline=False)
        embed.add_field(name=f'To {result.target_language}', value=result.translated, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))