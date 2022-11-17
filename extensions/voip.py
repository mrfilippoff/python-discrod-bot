from discord.ext import commands
import random

MAX_USER_LIMIT = 99 #by discord
DEFAULT_USER_LIMIT = 4
custom_channel_emojis = [
    '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨',
    '🐯', '🦁', '🐮', '🐸', '🐵', '🐔', '🐧', '🐤', '🦆',
    '🦉', '🐺', '🐗', '🐴', '🦄'
]

def get_bitrate(curr, default):
        try:
            bitrate = int(curr) * 1000
            return bitrate if bitrate <= default else default
        except:
            return default

def get_user_limit(num, default):
    try:
        num = int(num)
        return num if num <= 99 else MAX_USER_LIMIT
    except:
        return default

def emoji_for_channel_name():
    random.choice(custom_channel_emojis)


def is_emoji_in_channel_name(name):
    return any([emoji in name for emoji in custom_channel_emojis])


class Voip(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.vc_ac = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel:
            if len(before.channel.members) == 0 and is_emoji_in_channel_name(before.channel.name):
                await before.channel.delete()

        if after.channel:
            if self.vc_ac and after.channel.name.startswith(self.vc_ac):
                await self.create_vc(**{"author": member})

    @commands.command(
        help='Create voice channel'
    )
    async def vc(self, ctx, user_limit=4, channel_name=None, bitrate_kbps=None):
        kwargs = dict()

        kwargs["author"] = ctx.message.author
        kwargs["channel_name"] = channel_name
        kwargs["bitrate_kbps"] = bitrate_kbps
        kwargs["user_limit"] = user_limit

        if not kwargs["author"].voice:
            return await ctx.send(f'Please, join the some voice channel')

        if kwargs["author"].voice.afk:
            return await ctx.send(f'First wake up! Neo!')

        current_channel = kwargs["author"].voice.channel

        if current_channel.category is None:
            return await ctx.send(f'Current channel should be categorised')

        return await self.create_vc( **kwargs )


    async def create_vc(self, **kwargs):
        author = kwargs.get("author")
        channel_name = kwargs.get("channel_name")
        category = author.voice.channel.category
        default_name = f"{author.name}'s"

        if category:
            default_name = f"{category.name}-{len(category.voice_channels) + 1}"

        emoji = random.choice(custom_channel_emojis)
        name = channel_name if channel_name else default_name
        name = f'{emoji} {name}'

        channel_bitrate = get_bitrate(kwargs.get("bitrate_kbps"), author.guild.bitrate_limit)
        user_limit = get_user_limit(kwargs.get("user_limit"), DEFAULT_USER_LIMIT)
        channel = await author.guild.create_voice_channel(
            name,
            category=category,
            user_limit=user_limit,
            bitrate=channel_bitrate
        )
        return await author.move_to(channel)

    @commands.command(help="Set prefix symbol for auto voice channel creating")
    @commands.has_permissions(manage_guild=True)
    async def vc_ac(self, ctx, symbol=None):
        if symbol is None:
            return await ctx.send(f'Set the symbol!')

        self.vc_ac = symbol
        return await ctx.send(f'Done!')


def setup(client):
    client.add_cog(Voip(client))
