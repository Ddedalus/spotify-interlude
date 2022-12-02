""" Console entrypoint for the package. """
import logging
import sched
from typing import List

import typer

from interlude.audio_session import unregister_callbacks
from interlude.core import PauseSpotifyCallback, manage_sessions_task
from interlude.spotify import SpotifyClient

log = logging.getLogger("interlude")
log.setLevel(logging.INFO)
handler = logging.FileHandler("interlude.logs")
log.addHandler(handler)

app = typer.Typer()

PROCESS_NAMES = ["chrome.exe", "firefox.exe", "Telegram.exe"]


@app.command()
def main(
    spotify_secret: str = typer.Option(..., envvar="SPOTIFY_SECRET"),
    spotify_client_id: str = typer.Option(
        "b28755671fa94530b587e9b8c30d1951", envvar="SPOTIFY_CLIENT_ID"
    ),
    process_names: List[str] = typer.Option(PROCESS_NAMES, "-p", "--process-name"),
    device_names: List[str] = typer.Option(["SURFACE"], "-d", "--device-name"),
    session_refresh_interval: float = 5.0,
    warmup_duration: float = 2.0,
):
    scheduler = sched.scheduler()

    PauseSpotifyCallback.client = SpotifyClient(
        spotify_client_id, spotify_secret, device_names
    )
    PauseSpotifyCallback.scheduler = scheduler
    PauseSpotifyCallback.warmup_duration = warmup_duration

    sessions = manage_sessions_task(scheduler, session_refresh_interval, process_names)
    try:
        log.info("Starting the scheduler listaning for audio sessions...")
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        log.warning("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())


if __name__ == "__main__":
    app()
