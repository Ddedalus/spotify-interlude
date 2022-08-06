""" Console entrypoint for the package. """
from interlude.core import manage_sessions_task, PauseSpotifyCallback
from interlude.audio_session import unregister_callbacks
import typer
import sched

app = typer.Typer()


@app.command()
def main(session_refresh_interval: float = 5.0, warmup_duration: float = 2.0):
    scheduler = sched.scheduler()
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
