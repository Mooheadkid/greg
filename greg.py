# This example requires the 'message_content' intent.

import discord
from discord.ext import commands
import asyncio
import urllib
import re
import os
from YTDLSource import YTDLSource

intents = discord.Intents.default()

client = commands.Bot(command_prefix="//", intents=intents)

song_queue = []

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'tmp/%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'prefer_ffmpeg': True,
    'audioformat': 'wav',
    'forceduration': True
}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    try:
        synced_commands = await client.tree.sync()
        print(f"Synced {len(synced_commands)} commands")
    except Exception as e:
        print("An error has occurred with syncing application commands:", e)

@client.tree.command(name="queue", description="Queues up a song")
async def queue(interaction: discord.Interaction, song: str, artist: str = None):
    if artist is not None:
        await interaction.response.send_message(f"Searching for {song} by {artist} on Youtube...")
        song = song.replace(" ", "_")
        artist = artist.replace(" ", "_")
        html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={song}_{artist}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    else:
        await interaction.response.send_message(f"Searching for {song} on Youtube...")
        song = song.replace(" ", "_")
        html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={song}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]
    if len(video_ids) <= 0:
        await interaction.channel.send("Can't find the song :(")
    else:
        song_queue.append(url)
        await interaction.channel.send(f"Queued {url} :)")
        
@client.tree.command(name="dj", description="Starts the queue.")
async def dj(interaction: discord.Interaction):
    if len(song_queue) <= 0:
        await interaction.response.send_message("There's no queued songs lol")
        return
    await interaction.response.send_message("Started the queue")
    try:
        server = interaction.guild
        voice_client = discord.utils.get(client.voice_clients, guild=server)
        for index in range(0, len(song_queue)):
            filename, length = await YTDLSource.from_url(song_queue[index])
            await interaction.channel.send('Playing {} rn'.format(song_queue[index]))
            source = discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename)
            voice_client.play(source)
            await asyncio.sleep(length)
            os.remove(filename)
    except:
        await interaction.channel.send("I need to be in a voice channel to start bro")
    song_queue.clear()

@client.tree.command(name="join", description="greg joins the party.")
async def join(interaction: discord.Interaction):
    try:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message("The life of the party's here!")
    except:
        await interaction.response.send_message("I'm already here bro")

@client.tree.command(name="kick", description="greg gets kicked out of the party.")
async def leave(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        await voice_client.disconnect()
        await interaction.response.send_message(":,(")
    except:
        await interaction.response.send_message("Way to rub it in :(")

@client.tree.command(name="shut", description="Shuts greg up and makes him forget all queued songs")
async def shut(interaction: discord.Interaction):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
        song_queue.clear()
        await voice_client.stop()
        await interaction.response.send_message("ok :(")
    except:
        await interaction.response.send_message("Man fuck you guys :(")


with open('../token.txt') as file:
    token = file.read()

client.run(token)
