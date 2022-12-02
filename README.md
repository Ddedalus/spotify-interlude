_Pause Spotify playback when other apps start making noise on Windows._
_Automatically resume playback when the other sound finishes._

This mimics default Android functionality, where background music would stop for
a duration of a call or alarm and resume afterwards.

# Usage

## Install

```powershell
pip install spotify-interlude
```

## Set up Spotify
You'll need to obtain a [Development Token](https://developer.spotify.com/) from Spotify.
1. Start by [creating an account](https://accounts.spotify.com/en/status).
2. Head to the [dashboard](https://developer.spotify.com/dashboard/applications) and create an App called Interlude on your account.
3. Copy the client ID and secret. This package will need them to control your Spotify client.
 
## Run Interlude
Start Spotify and play some music. Then launch interlude:
```powershell
$Env:SPOTIFY_SECRET=...
$ENV:SPOTIFY_CLIENT_ID=...
interlude
```
When you try to play some sounds in Chrome, the music should stop playing.

## Configure interlude

You can tweak the behaviour of interlude using command line options:

```powershell
interlude --help
# Usage: interlude [OPTIONS]
# 
#   Monitor the local Spotify client and apps making foreground noise. If
#   --shortcut-path is specified, create a Windows shortcut with the same
#   options instead.
# 
# Options:
#   --spotify-secret TEXT           Secret from your Spotify App dashboard.
#                                   [env var: SPOTIFY_SECRET; required]
#   --spotify-client-id TEXT        Client Id from your Spotify App dashboard.
#                                   [env var: SPOTIFY_CLIENT_ID; required]
#   -p, --process-name TEXT         Names of the programs which should pause
#                                   Spotify when palying sound.  [default:
#                                   chrome.exe, firefox.exe, Telegram.exe]
#   -d, --device-name TEXT          Name of the Spotify device, in case you have
#                                   multiple connected simultaneously. This can
#                                   be used to pause palyback outside of this
#                                   computer.  [default: SURFACE]
#   --session-refresh-interval FLOAT
#                                   How often to scan for new foreground apps
#                                   (seconds)  [default: 5.0]
#   --warmup-duration FLOAT         Delay between end of foreground sound and
#                                   playback resume.  [default: 2.0]
#   --shortcut-path PATH            Path where a shortcut to Interlude should be
#                                   created.
#   --log-path PATH                 Write logs to this file instead of stdout
#   --log-level TEXT                Minimal level of the logs to display
#                                   [default: INFO]
#   --install-completion [bash|zsh|fish|powershell|pwsh]
#                                   Install completion for the specified shell.
#   --show-completion [bash|zsh|fish|powershell|pwsh]
#                                   Show completion for the specified shell, to
#                                   copy it or customize the installation.
#   --help                          Show this message and exit.
```

## Create shortcut
To easily start interlude, create a shortcut with your desired settings:
```powershell
interlude --shortcut-path ~/Desktop/Interlude.lnk # add other options as needed
```
Note: the Spotify secret and client ID will be baked into the shortcut.

## Environment file

The CLI parses environment variables, so you can keep secrets etc. out of command line history.

You may find a [dotenv file loader](https://github.com/rajivharris/Set-PsEnv) handy in PowerShell.
