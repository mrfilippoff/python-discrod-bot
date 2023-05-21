from dotenv import load_dotenv
import os
import datetime
import aiohttp
import logging
from collections import Counter, defaultdict
from extensions.utils.context import Context
from extensions.utils.config import Config
from extensions.utils import checks
from typing import Union, Optional

from discord import (Intents, AllowedMentions, Message, Guild,
                     HTTPException, utils, Interaction, Member,
                     ShardInfo, Embed, Object, ui, ButtonStyle)

from discord.ext import commands

from ui import RolesView, RoleGreetingModal

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD = int(os.getenv("GUILD"))

GUILD_OBJ = Object(id=GUILD or 0)

initial_extensions = (
    'extensions.service',
    'extensions.manage',
    'extensions.music',
    'extensions.misc',
    'extensions.poll',
    'extensions.random_status_game',
    'extensions.voip',
    'extensions.minigames'
)

command_prefix = os.getenv("COMMAND_PREFIX") or '+'

log = logging.getLogger(__name__)


class TeaBot(commands.AutoShardedBot):
    def __init__(self):
        allowed_mentions = AllowedMentions(
            roles=False, everyone=False, users=True)
        intents = Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
            message_content=True,
        )

        super().__init__(
            command_prefix=command_prefix,
            description='TeaBot helps you',
            pm_help=None,
            help_attrs=dict(hidden=True),
            chunk_guilds_at_startup=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
        )

        self.resumes: defaultdict[int,
                                  list[datetime.datetime]] = defaultdict(list)
        self.identifies: defaultdict[int,
                                     list[datetime.datetime]] = defaultdict(list)
        self.spam_control = commands.CooldownMapping.from_cooldown(
            2, 12.0, commands.BucketType.user)
        self._auto_spam_count = Counter()

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.blacklist: Config[bool] = Config('blacklist.json')
        self.options: Config[bool] = Config('teabot.json')

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception('Failed to load extension %s.', extension)

    async def log_spammer(self, ctx: Context, message: Message, _: float, *, autoblock: bool = False):
        if not autoblock:
            return

        return await ctx.send(f'{message.author}, you are an auto-blocked member and i will ignore you simp')

    async def process_commands(self, message: Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist:
            return

        bucket = self.spam_control.get_bucket(message)
        current = message.created_at.timestamp()
        retry_after = bucket and bucket.update_rate_limit(current)
        author_id = message.author.id

        if retry_after:
            self._auto_spam_count[author_id] += 1

            if self._auto_spam_count[author_id] >= 5:
                await self.add_to_blacklist(author_id)
                del self._auto_spam_count[author_id]
                await self.log_spammer(ctx, message, retry_after, autoblock=True)
                return
            else:
                await self.log_spammer(ctx, message, retry_after)
                return

        await self.invoke(ctx)

    async def add_to_blacklist(self, object_id: int):
        await self.blacklist.put(object_id, True)

    async def remove_from_blacklist(self, object_id: int):
        try:
            await self.blacklist.remove(object_id)
        except KeyError:
            pass

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = utils.utcnow()

        log.info('Ready: %s (ID: %s)', self.user, self.user.id)

    async def on_shard_resumed(self, shard_id: int):
        log.info('Shard ID %s has resumed...', shard_id)
        self.resumes[shard_id].append(utils.utcnow())

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_guild_join(self, guild: Guild) -> None:
        if guild.id in self.blacklist:
            await guild.leave()

    async def close(self) -> None:
        await super().close()
        await self.session.close()

    def _clear_gateway_data(self) -> None:
        one_week_ago = utils.utcnow() - datetime.timedelta(days=7)

        for _, dates in self.identifies.items():
            to_remove = [index for index, dt in enumerate(
                dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

        for _, dates in self.resumes.items():
            to_remove = [index for index, dt in enumerate(
                dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

    async def before_identify_hook(self, shard_id: int, *, initial: bool):
        self._clear_gateway_data()
        self.identifies[shard_id].append(utils.utcnow())
        await super().before_identify_hook(shard_id, initial=initial)

    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, HTTPException):
                log.exception(
                    'In %s:', ctx.command.qualified_name, exc_info=original)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(str(error))

    async def get_context(self, origin: Union[Interaction, Message], /, *, cls=Context) -> Context:
        return await super().get_context(origin, cls=cls)

    async def get_or_fetch_member(self, guild: Guild, member_id: int) -> Optional[Member]:
        member = guild.get_member(member_id)
        if member is not None:
            return member

        # type: ignore  # will never be None
        shard: ShardInfo = self.get_shard(guild.shard_id)
        if shard.is_ws_ratelimited():
            try:
                member = await guild.fetch_member(member_id)
            except HTTPException:
                return None
            else:
                return member

        members = await guild.query_members(limit=1, user_ids=[member_id], cache=True)
        if not members:
            return None
        return members[0]


bot = TeaBot()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.tree.command()
async def hello(interaction: Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.tree.command()
async def my_roles(interaction: Interaction):
    """Manage user roles"""
    view = RolesView(interaction.guild, interaction.user)
    await interaction.response.send_message(
        'Update your game roles right now!',
        view=view,
        ephemeral=True
    )


@bot.tree.command()
@checks.is_manager()
async def teabot(interaction: Interaction):
    """Teabot role options [for admin only]"""
    await interaction.response.send_modal(RoleGreetingModal(bot))


@bot.tree.context_menu(name='Report to Moderators')
async def report_message(interaction: Interaction, message: Message):
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.mention} to our moderators.',
        ephemeral=True
    )

    try:
        log_channel = interaction.guild.get_channel(
            int(bot.options.get("report_channel")) or 0
        )

        embed = Embed(title='Reported Message')
        if message.content:
            embed.description = message.content

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at

        url_view = ui.View()
        url_view.add_item(ui.Button(label='Go to Message',
                                    style=ButtonStyle.url, url=message.jump_url))

        await log_channel.send(embed=embed, view=url_view)
    except Exception as e:
        print(e)


bot.run(TOKEN)
