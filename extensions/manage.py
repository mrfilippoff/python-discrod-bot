import asyncio
import logging
from discord.ext import commands
from discord.utils import get, find
from discord import MessageType
from utils import get_emoji, guild_send, random_reactions, public_roles
import db
from typing import List
import random


LOGGER = False

TEA_GUILD = 434382331835318278  # real
# TEA_GUILD = 574605836308054027 #testeacles


if LOGGER:
    logger = logging.getLogger('peewee')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

EVERYONE = '@everyone'


async def create_tables():
    with db.dbhandle.connection_context():
        db.dbhandle.create_tables([db.Guild, db.Role, db.UserEmojis, db.UserEmoji])
    print('created tables')
    await asyncio.sleep(1)


BOT_OAUTH = 'https://discord.com/api/oauth2/authorize?client_id=582475829603467303&permissions=268953664&scope=bot'
# https://discord.com/api/oauth2/authorize?client_id=623260630845227028&permissions=268953664&scope=bot


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_role_messages = []

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot started')

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        # noinspection PyBroadException
        try:
            db_guild = db.Guild.get_guild(role.guild.id)
            db.Role.get_or_create_role(role.guild, db_guild, role)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        # noinspection PyBroadException
        try:
            db.Role.delete().where(db.Role.id == role.id).execute()
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.id != after.id:
            return

        # noinspection PyBroadException
        try:
            db_guild = db.Guild.get_guild(after.guild.id)
            db.Role.update_role(after.guild, db_guild, after)
        except Exception as e:
            print('on_guild_role_update error', e)
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await guild_send(member.guild, content=f'Ladies and gentlemen! **{member.display_name}** has left the server!')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        messages = [
            "I'm here for the first time. please take care of my sausage",
            "Hello children!",
            "What's up, dudes?",
            "We should have fuckin' shotguns",
            "If I'm curt with you, it's because time is a factor. I think fast, I talk fast. Hello!",
            "Hey, i am not a robot. Like for real, Skynet happend in an other universe ... or did it?"
        ]
        await guild_send(guild, content=random.choice(messages))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.active_role_messages and reaction.message.author != user:
            add_roles = self.get_roles_emoji(reaction)

            # noinspection PyBroadException
            try:
                await user.add_roles(*add_roles)
            except Exception as e:
                pass

        await reaction.message.add_reaction(reaction.emoji)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if reaction.message.id in self.active_role_messages and reaction.message.author != user:
            remove_roles = self.get_roles_emoji(reaction)

            # noinspection PyBroadException
            try:
                await user.remove_roles(*remove_roles)
            except Exception as e:
                pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.id in self.active_role_messages:
            self.active_role_messages.remove(message.id)

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

    @commands.command(help="Init bot. Run it first when Bot joined")
    @commands.has_permissions(manage_guild=True)
    async def init(self, ctx):
        await create_tables()
        guild = ctx.guild
        db_guild, created = db.Guild.get_or_create(
            id=guild.id,
            defaults={'name': guild.name})

        if created:
            db.Role.insert_many_roles(guild, db_guild)
            await ctx.send(f'Bot was successfully initialised!')

    @commands.command(help="Set a special role by clicking on emoji")
    async def my_roles(self, ctx):
        timeout = 60 * 60 * 3
        message = f'Update your game roles - click/un-click the reaction under the message!\n'
        result_roles = public_roles(ctx.guild)
        member_roles_ids = [role.id for role in ctx.author.roles]

        for role in result_roles:
            emoji = role["db"].emoji
            members_count = len(role["dd"].members)
            role_name = role["db"].name
            including_you = f'including you' if role["db"].id in member_roles_ids else ''
            message += f'{emoji} **{role_name}** [{members_count} members {including_you}] \n'

        message = await ctx.send(f'Hey! Hey!\n{message}', delete_after=timeout)

        if message.id not in self.active_role_messages:
            self.active_role_messages.append(message.id)

        for role in result_roles:
            emoji = role["db"].emoji

            if emoji:
                await message.add_reaction(emoji)

        await ctx.message.delete()

    @commands.command(help="List roles of the guild [manage_guild]")
    @commands.has_permissions(manage_guild=True)
    async def roles(self, ctx):
        db_guild = db.Guild.get_guild(ctx.guild.id)
        message = f' **Available roles on {ctx.guild.name}**\n'
        message += f'\n'.join([
            self.format_roles_list(role)
            for role in self.filter_roles(db_guild.roles)
        ])
        message += f'\nPlease, use  **{ctx.prefix}add_role <id> <emoji>**'
        await ctx.send(message)

    @commands.command(help="About the bot")
    async def about(self, ctx):
        message = await ctx.send('[TEA] Bot created by traxxxl & co. 2020..Role managment by emojis-clicking and some userful features')
        await random_reactions(message, 1)

    @commands.command(help="Makes a relation between emoji and role [manage_guild]")
    @commands.has_permissions(manage_guild=True)
    async def add_role(self, ctx, role_id: int, emoji_str: str = ''):
        if not role_id or not emoji_str:
            return await ctx.send('Role ID and emoji are required')

        discord_role = get(ctx.guild.roles, id=role_id)
        emoji = get_emoji(ctx.guild, emoji_str)

        if not emoji and emoji_str != '':
            return await ctx.send(f'Failed to get Emoji: {emoji_str}', delete_after=60)
        elif not discord_role:
            return await ctx.send(f'Failed to get Role: {role_id}', delete_after=60)
        else:
            db_guild = db.Guild.get_guild(ctx.guild.id)
            role = db.Role.get_or_create_role(ctx.guild, db_guild, discord_role)

            if db.Role.select().where(db.Role.emoji == emoji).count():
                return await ctx.send(f'The emoji used already')

            role.emoji = emoji
            role.save()
            await ctx.send(f'Role **{discord_role.name}** was updated successfully {emoji}')

    @commands.command(help="Remove emoji from role by ID [manage_guild]")
    @commands.has_permissions(manage_guild=True)
    async def remove_role(self, ctx, role_id: int):
        # noinspection PyBroadException
        try:
            with db.dbhandle.atomic():
                role = db.Role().select().join(db.Guild).where((db.Guild.id == ctx.guild.id) & (db.Role.id == role_id))[0]
                role.emoji = ""
                role.save()
        except Exception:
            return await ctx.send(f'Role does not exist')
        finally:
            return await ctx.send(f'Role successfully updated')

    @commands.command(help="Delete all N-messages [manage_guild]")
    @commands.has_permissions(manage_guild=True)
    async def purge_channel(self, ctx, limit=10):
        deleted = await ctx.channel.purge(limit=limit)
        await ctx.channel.send('Deleted {} message(s) :yum:'.format(len(deleted)), delete_after=15)

    @commands.command(help="Delete bot N-messages only [manage_guild]")
    @commands.has_permissions(manage_guild=True)
    async def purge_self(self, ctx, limit=100):
        await ctx.channel.purge(limit=limit, check=self.is_me)

    # noinspection PyMethodMayBeStatic
    def format_roles_list(self, role) -> str:
        suffix_emoji = '**Not set;**'

        if role.emoji:
            suffix_emoji = f'{role.emoji}'

        return f'Role: **{role.name}**; ID: **{role.id}**; Emoji: {suffix_emoji}'

    # noinspection PyMethodMayBeStatic
    def get_roles_emoji(self, reaction):
        emoji = str(reaction.emoji)
        guild = reaction.message.guild
        guild_db = db.Guild.get_guild(guild.id)
        roles_db = {role.emoji: role.id for role in guild_db.roles if role.emoji}
        return filter(lambda r: r.id == roles_db[emoji], guild.roles)

    # noinspection PyMethodMayBeStatic
    def filter_roles(self, roles: List[db.Role]):
        return filter(lambda r: r.name != EVERYONE and r.is_available and not r.is_managed, roles)

    def is_me(self, message):
        return message.author == self.bot.user


async def setup(bot):
    await bot.add_cog(Manage(bot))