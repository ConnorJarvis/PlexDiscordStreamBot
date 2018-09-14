from plexapi.myplex import MyPlexAccount
import configparser
import discord
import asyncio
import subprocess
import os
import time
import string
from multiprocessing import Process
import validators
from urllib.parse import urlsplit
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

def startMovie(path, channel):
    devnull = open('/dev/null', 'w')
    # Start streaming the movie using ffmpeg
    # Path to movie is pulled from the plex api because the paths are the same on both machines
    subprocess.call(["/root/bin/ffmpeg", "-re", "-i", path, "-c:v", "libx264", "-filter:v", "scale=1280:trunc(ow/a/2)*2", "-preset", "fast", "-minrate", "500k", "-maxrate", "3000k", "-bufsize", "6M", "-c:a", "libfdk_aac", "-b:a", "160k", "-f", "flv", config['stream']['Destination']], stdout=devnull)
    # Notifiy that the movie has finished
    client.send_message(channel, 'Stream has finished')
    # Set the movie playing variable to false to allow a new movie to be streamed
    moviePlaying = False
    # Clear the game playing information
    client.change_presence(game=discord.Game(name=None))


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
        if len(movies.search(name))>0:
            # Loop through the search results and add them to the message
            for video in movies.search(name):
                msg += '`'+video.title+'`\r'
        else:
            msg = 'No movie found'
        # Send message with search results
        await client.send_message(message.channel, msg)
    # Message is command to play movie
    elif message.content.startswith('!play'):
        # If a movie is already playing discard message and notify
        if moviePlaying == True:
            await client.send_message(message.channel, 'Stream is already playing')
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

            p = Process(target=startMovie, args=(movie.locations[0],message.channel,))
            p.start()

    # Movie stop command
    elif message.content.startswith('!stop'):
        try:
            ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
            # Kill the ffmpeg process
            subprocess.run(["kill",ffmpegID])
        except:
            print("No movie playing")
        # Clear the game playing information
        await client.change_presence(game=discord.Game(name=None))
        # Set the movie playing variable to false to allow a new movie to be streamed
        moviePlaying = False
        # Send message to confirm action
        await client.send_message(message.channel, 'Stopping Stream')
    # Pause command
    elif message.content.startswith('!pause'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        # Suspend the ffmpeg process
        subprocess.run(["kill", "-s", "SIGSTOP",ffmpegID])
        # Send message to confirm action
        await client.send_message(message.channel, 'Pausing Stream')
    elif message.content.startswith('!resume'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        # Resume the ffmpeg process
        subprocess.run(["kill", "-s", "SIGCONT", ffmpegID])
        # Send message to confirm action
        await client.send_message(message.channel, 'Resuming Stream')
    # Print out commands available
    elif message.content.startswith('!help'):
        await client.send_message(message.channel, '**!search {movie}** Search for a movie by name\r**!play {movie}** Play a movie using the exact name from the search command\r**!pause** Pause the movie\r**!resume** Resume the paused movie\r**!stop** Stop the movie')
    elif message.content.startswith('!tvsearch'):
        # Define blank message
        msg = ''
        # Get the name of the movie from the message
        name = message.content[len('!tvsearch'):].strip()
        # Define the tv library
        tv = plex.library.section('TV Shows')
        if len(tv.search(name)) > 0:
            # Loop through the search results and add them to the message
            for video in tv.search(name):
                msg = msg + "```\r"+video.title
                for season in video.seasons():
                    msg = msg + "\rSeason "+ str(season.index)+"\r"
                    for episode in season.episodes():
                        msg = msg + str(episode.index) + " "
            msg = msg + '```'
        else:
            msg = 'No TV show found'
        # Send message with search results
        await client.send_message(message.channel, msg)
    elif message.content.startswith('!tvplay'):
        # Define blank message
        msg = ''
        # Get the name of the movie from the message
        

        season = message.content.find("-s=")
        episode = message.content.find("-e=")
        name = message.content[len('!tvplay'):season].strip()
        seasonNumber = message.content[season+3:episode].strip()
        episodeNumber = message.content[episode+3:].strip()
        # Define the tv library
        tv = plex.library.section('TV Shows')
        if len(tv.search(name)) > 0:
            # Loop through the search results and add them to the message
            for video in tv.search(name):
                for season in video.seasons():
                    for episode in season.episodes():
                        if str(season.index) == str(seasonNumber) and str(episode.index) == str(episodeNumber):
                            await client.change_presence(game=discord.Game(name=episode.title))
                            # Set the global movie playing variable so there aren't duplicate movies trying to stream
                            moviePlaying = True
                            ## Send message to confirm action
                            await client.send_message(message.channel, 'Streaming '+episode.title)

                            p = Process(target=startMovie, args=(episode.locations[0],message.channel,))
                            p.start()
        else:
            await client.send_message(message.channel, 'No episode or TV show matching that name found')
    elif message.content.startswith('!youtubeplay'):
        name = message.content[len('!youtubeplay'):].strip()
        if validators.url(name) == True:
            parsed_uri = urlsplit(name)
            if parsed_uri.hostname == "www.youtube.com" or parsed_uri.hostname == "youtube.com" or parsed_uri.hostname == "youtu.be"  or parsed_uri.hostname == "www.youtu.be":
                await client.change_presence(game=discord.Game(name='Youtube'))
                # Set the global movie playing variable so there aren't duplicate movies trying to stream
                moviePlaying = True
                ## Send message to confirm action
                await client.send_message(message.channel, 'Streaming Youtube')
                
                devnull = open('/dev/null', 'w')
                # Start streaming the movie using ffmpeg
                # Path to movie is pulled from the plex api because the paths are the same on both machines
                command = "youtube-dl -f 'best[ext=mp4]' -o - \""+name+"\" | ffmpeg -re -i pipe:0 -c:v copy -preset fast -c:a copy -f flv "+ config['stream']['Destination']
                print(command)
                subprocess.call(command.split(), shell=False)
        else:
            await client.send_message(message.channel, 'Invalid url')


       

# Start discord client
client.run(config['discord']['Key'])

