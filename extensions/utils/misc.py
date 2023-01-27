import re
import random
from discord.utils import get
from discord import Message, File
from emoji import EMOJI


def get_emoji(guild, emoji):
    re_emoji = re.match(r'<a?:[a-zA-Z0-9_]+:([0-9]+)>$', emoji)

    if re_emoji:
        emoji_id = re_emoji.group(1)
        return get(guild.emojis, id=int(emoji_id))

    return emoji


async def random_reactions(message: Message, count: int = 0, emoji_limi_random: int = 0):
    rand_int = random.randint(2, 3)
    emoji_list = EMOJI if emoji_limi_random == 0 else EMOJI[:emoji_limi_random]
    range_iter = range(count) if count else range(random.randint(1, rand_int))

    for _ in range_iter:
        await message.add_reaction(random.choice(emoji_list))


async def guild_send(guild, **kwargs):
    if guild.system_channel:
        # noinspection PyBroadException
        try:
            await guild.system_channel.send(**kwargs)
        except Exception:
            pass

async def guild_send_image(guild, path: str):
    with open(path, 'rb') as f:
        picture = File(f)
        await guild_send(guild, file=picture)