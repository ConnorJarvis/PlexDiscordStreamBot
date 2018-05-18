from plexapi.myplex import MyPlexAccount
import configparser
import discord
import asyncio
import subprocess
import os
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) +'/config.ini')

account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect() 

moviePlaying = False
ffmpegID = 1
client = discord.Client()
try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    global moviePlaying
    global ffmpegID
    global DEVNULL
    if message.content.startswith('!search'):
        msg = ''
        name = message.content[len('!search'):].strip()
        movies = plex.library.section('Movies')
        for video in movies.search(name):
            print(video.title)
            print(video.ratingKey)
            msg += '`'+video.title+'`\r'
        await client.send_message(message.channel, msg)
    elif message.content.startswith('!play'):
        if moviePlaying == True:
            await client.send_message(message.channel, 'Movie is already playing')
        else:
	        msg = ''
	        name = message.content[len('!play'):].strip()
	        movie = plex.library.section('Movies').get(name)
	        await client.change_presence(game=discord.Game(name=movie.title))
	        moviePlaying = True
	        await client.send_message(message.channel, 'Playing '+movie.title)
	        subprocess.Popen(["/root/bin/ffmpeg", "-re", "-i", movie.locations[0], "-c:v", "libx264", "-filter:v", "scale=1280:trunc(ow/a/2)*2", "-preset", "fast", "-minrate", "500k", "-maxrate", "3000k", "-bufsize", "6M", "-c:a", "libfdk_aac", "-b:a", "160k", "-f", "flv", config['stream']['Destination']], stdout=DEVNULL)
    elif message.content.startswith('!stop'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        subprocess.run(["kill",ffmpegID])
        await client.change_presence(game=discord.Game(name=None))
        moviePlaying = False
        await client.send_message(message.channel, 'Stopping Movie')
    elif message.content.startswith('!pause'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        subprocess.run(["kill", "-s", "SIGSTOP",ffmpegID])
        await client.send_message(message.channel, 'Pausing Movie')
    elif message.content.startswith('!resume'):
        ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
        subprocess.run(["kill", "-s", "SIGCONT", ffmpegID])
        await client.send_message(message.channel, 'Resuming Movie')
    elif message.content.startswith('!help'):
        await client.send_message(message.channel, '**!search {movie}** Search for a movie by name\r**!play {movie}** Play a movie. \*Use the exact name from the search command\*\r**!pause** Pause the move\r**!resume** Resume a paused movie\r**!stop** Stop a movie')
client.run(config['discord']['Key'])