# greg: by Michael Yau
# Lamest Discord music bot of all time

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from Lib import queue as Queue
import asyncio

# Defines intended perms for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Creates a bot object with // as command prefix.
client = commands.Bot(command_prefix="//", intents=intents)

# Global list to hold song, I could use a queue data structure but eh.
song_queue = Queue.Queue()

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'tmp/%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'prefer_ffmpeg': True,
    'audioformat': 'wav',
    'forceduration': True
}

# Logging for when the bot goes online.
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    try:
        synced_commands = await client.tree.sync()
        print(f"Synced {len(synced_commands)} commands")
    except Exception as e:
        print("An error has occurred with syncing application commands:", e)

# Taken from StackOverflow: https://stackoverflow.com/questions/78561849/streaming-audio-content-from-youtube-to-discord
def search(query):
    with YoutubeDL({'format': 'bestaudio/best', 'noplaylist':'True', 'default_search':'ytsearch', 'js_runtimes': { 'node': { 'path': '../../AppData/Local/Author Software/nvm/.nodejs/node.exe'} }}) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    return info['url']

# Adds song to the queue
@client.tree.command(name="queue", description="Queues up a song")
async def queue(interaction: discord.Interaction, song: str, artist: str = None):
    song_query = song.replace(" ", "_")
    # Checks for optional parameter
    if artist is not None:
        await interaction.response.send_message(f"Searching for {song} by {artist} on Youtube...")
        artist = artist.replace(" ", "_")
        url = search(f"{song_query} {artist}") 
    else:
        await interaction.response.send_message(f"Searching for {song} on Youtube...")
        url = search(f"{song_query}")
    song_queue.put((url, song)) # package the song as a tuple storing the raw data and the song title.
    await interaction.channel.send(f"Queued {song} :)")
       
# Starts playing music
@client.tree.command(name="dj", description="Starts the queue.")
async def dj(interaction: discord.Interaction):
    # Handles no songs in queue
    if song_queue.empty():
        await interaction.response.send_message("My guy there's no queued songs lol")
        return
    await interaction.response.send_message("Party time :tada:") # cheesy dialogue for the cringe
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    channel = interaction.user.voice.channel
    server = interaction.guild
    voice_client = discord.utils.get(client.voice_clients, guild=server)
    # Try-except to play audio
    try:
        # Auto joins
        if channel is not None and voice_client is None:
            await channel.connect()
            await interaction.channel.send("The life of the party's here!")
            voice_client = discord.utils.get(client.voice_clients, guild=server)
        elif channel is None:
            await interaction.channel.send("Where are you going blud? U gotta settle down in the vc (voice chat for normies) to hear the set")
            return
        while not song_queue.empty(): # iterates through song queue
                song = song_queue.get()
                await interaction.channel.send('Playing {} rn'.format(song[1]))
                source = discord.FFmpegPCMAudio(source=song[0], **FFMPEG_OPTS) # connectes to ffmpeg
                voice_client.play(source) # plays sound from source
                while voice_client.is_playing() or voice_client.is_paused(): # waits until voice client is done
                    await asyncio.wait(1)
    except Exception as e:
        await interaction.channel.send("I gotta to be in a vc (voice channel for the normies) to start vro")
        await interaction.channel.send(f"{e}")
    await interaction.channel.send("That's my set :sunglasses:")

# Game ends greg
@client.tree.command(name="kick", description="greg gets kicked out of the party.")
async def leave(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        await voice_client.disconnect()
        await interaction.response.send_message(":sob:")
    except:
        await interaction.response.send_message("Way to rub it in :sad:")

# Let the tortured soul rest...
@client.tree.command(name="rest", description="greg drinks some water in preparation for the next set.")
async def rest(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        await voice_client.pause()
        await interaction.response.send_message(":baby_bottle::sweat_drops:")
    except:
        await interaction.response.send_message("Some die of thirst while others drown in it...")

# Skips current song in queue.
@client.tree.command(name="boo", description="Shames greg into skipping the song.")
async def boo(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        await voice_client.stop()
        await interaction.response.send_message("alrighty :sad:")
    except:
        await interaction.response.send_message("For why??? :cry:")

# Clears queue and shuts greg up
@client.tree.command(name="shut", description="Shuts greg up and makes him forget all queued songs")
async def shut(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        song_queue.clear()
        await voice_client.stop()
        await interaction.response.send_message("ok :sad:")
    except:
        await interaction.response.send_message("Man you guys suck :rage:")

# Connector to Discord bot
with open('../token.txt') as file:
    token = file.read()

client.run(token) # starts the bot
