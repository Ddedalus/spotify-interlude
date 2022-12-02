""" Console entrypoint for the package. """
import logging
import sched
from itertools import chain
from typing import List, Optional
from pathlib import Path
from win32com.client import Dispatch
import typer
import sys


from spotify_interlude.audio_session import unregister_callbacks
from spotify_interlude.core import PauseSpotifyCallback, manage_sessions_task
from spotify_interlude.spotify import SpotifyClient

app = typer.Typer()
REPO_ROOT = Path(__file__).parent.parent.resolve()
PROCESS_NAMES = ["chrome.exe", "firefox.exe", "Telegram.exe"]


@app.command()
def main(
    spotify_secret: str = typer.Option(
        ..., envvar="SPOTIFY_SECRET", help="Secret from your Spotify App dashboard."
    ),
    spotify_client_id: str = typer.Option(
        ...,
        envvar="SPOTIFY_CLIENT_ID",
        help="Client Id from your Spotify App dashboard.",
    ),
    process_names: List[str] = typer.Option(
        PROCESS_NAMES,
        "-p",
        "--process-name",
        help="Names of the programs which should pause Spotify when palying sound.",
    ),
    device_names: List[str] = typer.Option(
        ["SURFACE"],
        "-d",
        "--device-name",
        help="Name of the Spotify device, in case you have multiple connected simultaneously. This can be used to pause palyback outside of this computer.",
    ),
    session_refresh_interval: float = typer.Option(
        5.0, help="How often to scan for new foreground apps (seconds)"
    ),
    warmup_duration: float = typer.Option(
        2.0, help="Delay between end of foreground sound and playback resume."
    ),
    shortcut_path: Optional[Path] = typer.Option(
        None, help="Path where a shortcut to Interlude should be created."
    ),
    log_path: Optional[Path] = typer.Option(
        None, help="Write logs to this file instead of stdout"
    ),
    log_level: str = typer.Option("INFO", help="Minimal level of the logs to display"),
):
    """
    Monitor the local Spotify client and apps making foreground noise.
    If --shortcut-path is specified, create a Windows shortcut with the same options instead.

    """
    if shortcut_path is not None:
        typer.echo(f"Creating a shortcut for later use at {shortcut_path}")
        shell = Dispatch("WScript.Shell")
        s = shell.CreateShortCut(str(shortcut_path))

        s.Targetpath = sys.executable
        arguments = [
            "interlude/cli.py",
            *("--spotify-secret", spotify_secret),
            *("--spotify-client-id", spotify_client_id),
            *("--session-refresh-interval", str(session_refresh_interval)),
            *("--warmup-duration", str(warmup_duration)),
            *(("--log-path", str(log_path)) if log_path else ()),
            *("--log-level", log_level),
            *chain.from_iterable(("-p", n) for n in process_names),
            *chain.from_iterable(("-d", d) for d in device_names),
        ]
        s.Arguments = " ".join(arguments)
        s.WorkingDirectory = str(REPO_ROOT)
        s.Description = "Interlude: pause Spotify during audio calls"
        s.WindowStyle = 7
        s.save()
        exit(0)

    scheduler = sched.scheduler()

    logging.basicConfig(
        datefmt="%H:%M:%S",
        filename=log_path,
        level=log_level,
        format="%(asctime)s %(levelname)-4s: %(message)s",  # \n\tAt %(pathname)s:%(lineno)d",
    )
    logging.info(f"Logging configured with level {log_level}")

    PauseSpotifyCallback.client = SpotifyClient(
        spotify_client_id, spotify_secret, device_names
    )
    PauseSpotifyCallback.scheduler = scheduler
    PauseSpotifyCallback.warmup_duration = warmup_duration

    sessions = manage_sessions_task(scheduler, session_refresh_interval, process_names)
    try:
        logging.info("Starting the scheduler listaning for audio sessions...")
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        logging.warning("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())


if __name__ == "__main__":
    app()
