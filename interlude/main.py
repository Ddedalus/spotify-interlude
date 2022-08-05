import sched
import time
from typing import Dict, List, Iterable

import spotipy
from comtypes import COMError
from pycaw.callbacks import AudioSessionEvents
from pycaw.utils import AudioSession, AudioUtilities
from spotipy.oauth2 import SpotifyOAuth

foreground_process_names = ["chrome.exe", "firefox.exe", "Spotify.exe"]
sessions: Dict[int, AudioSession] = {}


def _unregister_callbacks(sessions: Iterable[AudioSession]):
    for s in sessions:
        s.unregister_notification()
        print(f"Unregistered callback for {s.Process and s.Process.name()}")


class StateLoggingCallback(AudioSessionEvents):
    def __init__(self, process_name: str = "") -> None:
        super().__init__()
        self.process_name = process_name

    def on_state_changed(self, new_state, new_state_id):
        print(f"{self.process_name} changed state to {new_state}")

    def on_session_disconnected(self, disconnect_reason, disconnect_reason_id):
        print(
            f"{self.process_name} session was disconnected because {disconnect_reason}"
        )


def discover_foreground_sessions(
    scheduler: sched.scheduler, sessions: Dict[int, AudioSession]
):
    """Find all audio sessions of foreground registered apps."""
    try:
        all_discovered: List[AudioSession] = AudioUtilities.GetAllSessions()
    except COMError:
        print("No audio output device registered!")
        scheduler.enter(3, 5, discover_foreground_sessions, (scheduler, sessions))
        return

    discovered_sessions = {
        s.ProcessId: s
        for s in all_discovered
        if s.Process and s.Process.name() in foreground_process_names
    }

    # Delete sessions which have sinde disappeared
    deleted = {pid: s for pid, s in sessions.items() if pid not in discovered_sessions}
    _unregister_callbacks(deleted.values())
    for pid in deleted:
        sessions.pop(pid)

    new = {pid: s for pid, s in discovered_sessions.items() if pid not in sessions}
    for pid, session in new.items():
        name = session.Process and session.Process.name() or "unknown"
        callback = StateLoggingCallback(name)
        session.register_notification(callback)
        print(f"Registered callback for {name}")
        sessions[pid] = session

    print(f"Tracking {len(sessions)} audio sessions")

    # check again in a moment
    scheduler.enter(3, 5, discover_foreground_sessions, (scheduler, sessions))


if __name__ == "__main__":
    try:
        scheduler = sched.scheduler()
        scheduler.enter(0, 5, discover_foreground_sessions, (scheduler, sessions))
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        _unregister_callbacks(sessions.values())
