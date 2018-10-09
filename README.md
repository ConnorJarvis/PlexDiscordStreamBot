# PlexDiscordStreamBot

This Discord bot connects to a plex server and allows the streaming of movies to an outside server using ffmpeg

A couple of assumptions are made that may need to be changed to work on different systems and these are:
- Your Plex movie library is named `Movies`
- Your Plex tv library is named `TV Shows`
- No other `ffmpeg` processes are running on the same system

Theoretically all you need to do to get started as far as I know:
- `Fill out config.example.ini and save as config.ini`
- `pip3 install -r requirements.txt `
- `python3 app.py`

If the path to the media is different on the plex server compared to the stream server add remapped folders in the config in the format of

`PLEX_FOLDER:STREAM_FOLDER,`

To update your videobot run `!update` only users specified in the `AuthorizedUsers` config option are allowed to run this command. Enter user IDs as a comma separated list
