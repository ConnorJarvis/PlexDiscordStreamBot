from plexapi.myplex import MyPlexAccount
import configparser
import discord
import asyncio
import subprocess
import os
import time
# Read in config
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) +'/config.ini')

# Connect to plex server
account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect() 

# Global variables to handle state
moviePlaying = False
ffmpegID = 0
# Define discord client
client = discord.Client()


# Just so you know your connected
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# On Discord message
@client.event
async def on_message(message):
    global moviePlaying
    global ffmpegID
    # Message is for searching
    if message.content.startswith('!search'):
        # Define blank message
        msg = ''
        # Get the name of the movie from the message
        name = message.content[len('!search'):].strip()
        # Define the movie library
        movies = plex.library.section('Movies')
        # Loop through the search results and add them to the message
        for video in movies.search(name):
            msg += '`'+video.title+'`\r'
        # Send message with search results
        await client.send_message(message.channel, msg)
    # Message is command to play movie
    elif message.content.startswith('!play'):
        # If a movie is already playing discard message and notify
        if moviePlaying == True:
            await client.send_message(message.channel, 'Movie is already playing')
        else:
            msg = ''
            name = message.content[len('!play'):].strip()
            # Get movie information from plex
            movie = plex.library.section('Movies').get(name)
            # Set the game the bot is playing to the movie name
            await client.change_presence(game=discord.Game(name=movie.title))
            # Set the global movie playing variable so there aren't duplicate movies trying to stream
            moviePlaying = True
            ## Send message to confirm action
            await client.send_message(message.channel, 'Streaming '+movie.title)
            devnull = open('/dev/null', 'w')
            # Start streaming the movie using ffmpeg
            # Path to movie is pulled from the plex api because the paths are the same on both machines
            subprocess.call(["/root/bin/ffmpeg", "-re", "-i", movie.locations[0], "-c:v", "libx264", "-filter:v", "scale=1280:trunc(ow/a/2)*2", "-preset", "fast", "-minrate", "500k", "-maxrate", "3000k", "-bufsize", "6M", "-c:a", "libfdk_aac", "-b:a", "160k", "-f", "flv", config['stream']['Destination']], stdout=devnull)
            # Notifiy that the movie has finished
            await client.send_message(message.channel, 'Movie has finished')
            # Set the movie playing variable to false to allow a new movie to be streamed
            moviePlaying = False
            # Clear the game playing information
            await client.change_presence(game=discord.Game(name=None))
    # Movie stop command
    elif message.content.startswith('!stop'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        # Kill the ffmpeg process
        subprocess.run(["kill",ffmpegID])
        # Clear the game playing information
        await client.change_presence(game=discord.Game(name=None))
        # Set the movie playing variable to false to allow a new movie to be streamed
        moviePlaying = False
        # Send message to confirm action
        await client.send_message(message.channel, 'Stopping Movie')
    # Pause command
    elif message.content.startswith('!pause'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        # Suspend the ffmpeg process
        subprocess.run(["kill", "-s", "SIGSTOP",ffmpegID])
        # Send message to confirm action
        await client.send_message(message.channel, 'Pausing Movie')
    elif message.content.startswith('!resume'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        # Resume the ffmpeg process
        subprocess.run(["kill", "-s", "SIGCONT", ffmpegID])
        # Send message to confirm action
        await client.send_message(message.channel, 'Resuming Movie')
    # Print out commands available
    elif message.content.startswith('!help'):
        await client.send_message(message.channel, '**!search {movie}** Search for a movie by name\r**!play {movie}** Play a movie using the exact name from the search command\r**!pause** Pause the movie\r**!resume** Resume the paused movie\r**!stop** Stop the movie')

# Start discord client
client.run(config['discord']['Key'])