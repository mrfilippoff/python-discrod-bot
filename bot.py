from dotenv import load_dotenv
import os
from discord.ext import commands
from discord import Intents
load_dotenv()

TOKEN = os.getenv("TOKEN")
EXTENSION_DIR = os.getenv("EXTENSIONS_DIR")

intents = Intents.default()
intents.presences = True
intents.guilds = True
intents.members = True
intents.emojis = True
intents.guild_messages = True
intents.reactions = True
intents.voice_states = True

client = commands.Bot(command_prefix='+', description='Tea Bot Helps You', intents=intents)


@client.command(help="Load an extension")
async def load(ctx, extension):
    try:
        client.load_extension(f'{EXTENSION_DIR}.{extension}')
        await ctx.send(f'{extension} extension loaded')
    except commands.ExtensionNotFound as e:
        await ctx.send(e)
    except (commands.ExtensionAlreadyLoaded, commands.errors.MissingRequiredArgument):
        pass


@client.command(help="Unload an extension")
async def unload(ctx, extension):
    try:
        client.unload_extension(f'{EXTENSION_DIR}.{extension}')
        await ctx.send(f'{extension} extension unloaded')
    except commands.ExtensionNotLoaded as e:
        await ctx.send(e)
    except commands.errors.MissingRequiredArgument:
        pass


@client.command(help="Reload extension")
async def reload(ctx, extension):
    try:
        client.reload_extension(f'{EXTENSION_DIR}.{extension}')
        await ctx.send(f'{extension} extension reloaded')
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        await ctx.send(e)


for filename in os.listdir(f'./{EXTENSION_DIR}'):
    if filename.endswith('.py'):
        client.load_extension(f'{EXTENSION_DIR}.{filename[:-3]}')

client.run(TOKEN)
