# PlexDiscordStreamBot

This Discord bot connects to a plex server and allows the streaming of movies to an outside server using ffmpeg

A couple of assumptions are made that may need to be changed to work on different systems and these are:
- Your Plex movie Library is named  `Movies`
- the ffmpeg process is located at `/root/bin/ffmpeg`
- No other `ffmpeg` processes are running on the same system

Theoretically all you need to do to get started as far as I know:
- `Fill out config.example.ini and save as config.ini`
- `pip3 install -r requirements.txt `
- `python3 app.py`


## Example usage
![Example usage](https://i.vangel.io/KZuaK.png)