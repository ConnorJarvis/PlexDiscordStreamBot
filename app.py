from plexapi.myplex import MyPlexAccount
import configparser
import discord
import asyncio
import subprocess
config = configparser.ConfigParser()
config.read('config.ini')

account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect() 

# movies = plex.library.section('Movies')
# for video in movies.search("Lord of the rings"):
#     print(video.title)
#     print(video.ratingKey)

# print(movies.get('The Lord of the Rings: The Return of the King'))

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
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
        msg = ''
        name = message.content[len('!play'):].strip()
        movie = plex.library.section('Movies').get(name)
        await client.send_message(message.channel, 'Playing '+movie.title)
        subprocess.run(["/root/bin/ffmpeg", "-re", "-i", movie.locations[0], "-c:v", "libx264", "-filter:v", "scale=1280:trunc(ow/a/2)*2", "-preset", "fast", "-minrate", "500k", "-maxrate", "3000k", "-bufsize", "6M", "-c:a", "libfdk_aac", "-b:a", "160k", "-f", "flv", "rtmp://stream.vangel.io/live/movie", "&"], shell=True)
    elif message.content.startswith('!stop'):
        subprocess.run(["killall", "ffmpeg"] )
        await client.send_message(message.channel, 'Stopping Movie')
client.run(config['discord']['Key'])