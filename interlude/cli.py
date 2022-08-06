""" Console entrypoint for the package. """
from interlude.core import manage_sessions_task, PauseSpotifyCallback
from interlude.audio_session import unregister_callbacks, AudioSession
import typer
import sched
from typing import Dict

app = typer.Typer()


@app.command()
def main(session_refresh_interval: int = 5):
    sessions: Dict[int, AudioSession] = {}
    scheduler = sched.scheduler()
    PauseSpotifyCallback.scheduler = scheduler

    manage_sessions_task(scheduler, sessions, session_refresh_interval)
    try:
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())


if __name__ == "__main__":
    app()
