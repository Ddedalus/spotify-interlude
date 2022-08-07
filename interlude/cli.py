""" Console entrypoint for the package. """
from interlude.core import manage_sessions_task, PauseSpotifyCallback
from interlude.audio_session import unregister_callbacks
from interlude.spotify import SpotifyClient
import typer
import sched

app = typer.Typer()


@app.command()
def main(
    spotify_secret: str = typer.Option(..., envvar="SPOTIFY_SECRET"),
    spotify_client_id: str = typer.Option(
        "b28755671fa94530b587e9b8c30d1951", envvar="SPOTIFY_CLIENT_ID"
    ),
    session_refresh_interval: float = 5.0,
    warmup_duration: float = 2.0,
):
    scheduler = sched.scheduler()

    PauseSpotifyCallback.client = SpotifyClient(spotify_client_id, spotify_secret)
    PauseSpotifyCallback.scheduler = scheduler
    PauseSpotifyCallback.warmup_duration = warmup_duration

    sessions = manage_sessions_task(scheduler, session_refresh_interval)
    try:
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())


if __name__ == "__main__":
    app()
