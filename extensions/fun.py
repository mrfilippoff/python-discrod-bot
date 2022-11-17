import random
import re

from discord.ext import commands
from discord.utils import find
from discord import Embed, Colour
from phrases import phrases
from emoji import EMOJI
from giphy import giphy
from extensions.manage import TEA_GUILD
from utils import guild_send, get_emoji
from db import UserEmoji, UserEmojis
from collections import Counter


def get_gif(q, rand=False):
    result = giphy(q)

    if not len(result):
        return

    if rand:
        return random.choice(result)

    return result[0]


def embed_gif(q):
    gif_dict = get_gif(q, rand=True)

    if not gif_dict:
        return

    gif = gif_dict.images.original.url
    embed = Embed(colour=Colour.blue())
    embed.set_image(url=gif)
    return embed


def user_format(user):
    return {
        'name': user.name,
        'avatar': user.avatar,
        'mention': user.mention,
        'bot': user.bot,
        'display_name': user.display_name
    }


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or reaction.message.author.bot:
            return

        author, _ = UserEmoji.get_or_create(
            user_id=reaction.message.author.id,
            defaults={
                'user_data': user_format(reaction.message.author)
            }
        )
        user_reacted, _ = UserEmoji.get_or_create(
            user_id=user.id,
            defaults={
                'user_data': user_format(user)
            }
        )
        user_emoji = UserEmojis(
            user=author,
            by_user=user_reacted,
            emoji=reaction.emoji,
            message_id=reaction.message.id
        )
        user_emoji.save()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not len(message.attachments):
            return

        attachment = await message.attachments[0].to_file()
        is_private = not message.guild

        if is_private:
            guild = self.client.get_guild(TEA_GUILD)
            member = find(lambda m: m == message.author, guild.members)

            if not member.premium_since:
                return await member.send('Fuck off, non-nitro-boosted twat! FUCK OFF!')

            return await guild_send(guild, file=attachment)

    @commands.command(help="Lol")
    async def g(self, ctx, *args):
        q = ' '.join(args)
        embed = embed_gif(q)

        if embed is None:
            return

        return await ctx.send(embed=embed)

    def count_emojis(self, query):
        emojis = [r.emoji for r in query.execute()]
        return Counter(emojis)

    @commands.command(help="Your achievements boi")
    async def achievements(self, ctx):
        mentions = ctx.message.mentions
        message = ''

        if len(mentions):
            return await ctx.send('Not work yet')
        else:
            author, _ = UserEmoji.get_or_create(
                user_id=ctx.message.author.id,
                defaults={
                    'user_data': user_format(ctx.message.author)
                }
            )
            result_emojis = self.count_emojis(author.set_to_me)  # dict {emoji: count}

            if not list(result_emojis):
                return await ctx.send(f"SORRY MATE...YOU SUCK")

            ems = []
            achievements = sorted(self.count_emojis(author.set_to_me).items(), key=lambda r: r[1], reverse=True)
            for item in filter(lambda x: x[1] > 1, achievements):
                emoji = get_emoji(ctx.guild, item[0])

                if not emoji:
                    continue

                ems.append(f'{emoji} x{item[1]}')

                if len(ems) == 30:
                    break

            if len(ems):
                message += "   ".join(ems)
            else:
                return await ctx.send(f"SORRY MATE...YOU ARE REALLY SUCK")

        return await ctx.send(message)

    @commands.command(help="Some fun")
    async def ping(self, ctx, *args):
        if len(args) != 1:
            return await ctx.send(f'Need one username or mention')

        mentions = ctx.message.mentions

        if not len(mentions):
            target = find(lambda m: m.name.lower() == args[0].lower(), ctx.channel.members)
        else:
            target = mentions[0]

        if target:
            author_mention = ctx.author.mention
            phrase = random.choice(phrases)
            emoji_1 = random.choice(EMOJI)
            emoji_2 = random.choice(EMOJI)
            message = phrase.format(user_1=author_mention, user_2=target.mention)
            bold_parts = re.findall(r'\*{2}(.*?)\*{2}', phrase)
            msg = f'{emoji_1} {message} {emoji_2}'

            if len(bold_parts):
                gif_query = bold_parts[0]
                embed = embed_gif(gif_query)
                if embed is not None:
                    return await ctx.send(msg, embed=embed)
            return await ctx.channel.send(msg)

        else:
            return await ctx.send(f"I cann't find the fuckin' body with name **{args[0]}**")



async def setup(bot):
    await bot.add_cog(Fun(bot))