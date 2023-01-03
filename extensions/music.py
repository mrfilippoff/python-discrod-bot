import math

import discord
from discord.ext import commands

from music import ytdl
from music import voice

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}


    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)

        if not state:
            state = voice.VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not after.channel and before.channel and member == self.bot.user:
            voice_state = self.voice_states[before.channel.guild.id]

            if voice_state:
                await voice_state.stop()

            del self.voice_states[before.channel.guild.id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != self.bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")

            if message.embeds:
                print(message.embeds[0].to_dict())

    @commands.hybrid_command(name='join', with_app_command=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""
        voice_state = self.get_voice_state(ctx)

        destination = ctx.author.voice.channel

        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            return

        voice_state.voice = await destination.connect()
        await ctx.send('Trying to join... just a moment')

    @commands.has_permissions(manage_guild=True)
    @commands.hybrid_command(name='summon', with_app_command=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        voice_state = self.get_voice_state(ctx)

        if not channel and not ctx.author.voice:
            raise voice.VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel

        if voice_state.voice:
            await voice_state.voice.move_to(destination)
            return

        voice_state.voice = await destination.connect()

        await ctx.send('Very well...')

    @commands.hybrid_command(name='leave', with_app_command=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        voice_state = self.get_voice_state(ctx)

        if not voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await voice_state.stop()
        del self.voice_states[ctx.guild.id]

        await ctx.send('Ok bruh...cya')

    @commands.hybrid_command(name='volume', with_app_command=True)
    @commands.is_owner()
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        voice_state = self.get_voice_state(ctx)

        if not voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.hybrid_command(name='now', with_app_command=True)
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        voice_state = self.get_voice_state(ctx)

        embed = voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='pause', with_app_command=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        voice_state = self.get_voice_state(ctx)


        if voice_state.is_playing and voice_state.voice.is_playing():
            voice_state.voice.pause()

        await ctx.send('Paused a currently playing song')


    @commands.hybrid_command(name='resume', with_app_command=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        voice_state = self.get_voice_state(ctx)

        if voice_state.is_playing and c.voice_state.voice.is_paused():
            voice_state.voice.resume()

        await ctx.send('Resumed a currently paused song')

    @commands.hybrid_command(name='stop', with_app_command=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        voice_state = self.get_voice_state(ctx)

        voice_state.songs.clear()

        if voice_state.autoplay:
            voice_state.autoplay = False
            await ctx.send('Autoplay is now turned off')
            
        if voice_state.is_playing:
            voice_state.voice.stop()
        
        await ctx.send('Stoped')

    @commands.hybrid_command(name='skip', with_app_command=True)
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author

        if voter == ctx.voice_state.current.requester:
            ctx.voice_state.skip()
            await ctx.send('Skipping track')

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                ctx.voice_state.skip()
                await ctx.send('Skipping track by votes')
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.hybrid_command(name='queue', with_app_command=True)
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='history', with_app_command=True)
    async def _history(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's history.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.song_history) == 0:
            return await ctx.send('Empty history.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.song_history) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.song_history[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.song_history), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='shuffle', with_app_command=True)
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()

        await ctx.send('Shuffled the queue')

    @commands.hybrid_command(name='remove', with_app_command=True)
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)

        await ctx.send(f'Removed a song from the queue by index {index}')

    @commands.hybrid_command(name='loop', with_app_command=True)
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.send('Looping a song is now turned ' + ('on' if ctx.voice_state.loop else 'off') )

    @commands.hybrid_command(name='autoplay', with_app_command=True)
    async def _autoplay(self, ctx: commands.Context):
        """Automatically queue a new song that is related to the song at the end of the queue.
        Invoke this command again to toggle autoplay the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.autoplay = not ctx.voice_state.autoplay
        await ctx.send('Autoplay after end of queue is now ' + ('on' if ctx.voice_state.autoplay else 'off') )

    @commands.hybrid_command(name='play', with_app_command=True)
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        voice_state = self.get_voice_state(ctx)

        if voice_state.voice is None:
            success = await ctx.invoke(self._summon)

            if not success:
                return
            
        async with ctx.typing():
            try:
                source = await ytdl.YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except ytdl.YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = voice.Song(source)
                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')
            
async def setup(bot):
    await bot.add_cog(Music(bot))

    