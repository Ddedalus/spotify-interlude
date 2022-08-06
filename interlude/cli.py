""" Console entrypoint for the package. """
from interlude.core import scheduler, manage_sessions_task
from interlude.audio_session import unregister_callbacks, AudioSession
import typer
from typing import Dict

app = typer.Typer()


@app.command()
def main():
    sessions: Dict[int, AudioSession] = {}
    scheduler.enter(0, 5, manage_sessions_task, (scheduler, sessions))
    try:
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())


if __name__ == "__main__":
    app()
