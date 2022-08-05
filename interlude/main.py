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


def unregister_callbacks(sessions: Iterable[AudioSession]):
    for s in sessions:
        print(f"Unregistered callback for {s.Process and s.Process.name()}")
        s.unregister_notification()


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
    unregister_callbacks(deleted.values())
    for pid in deleted:
        sessions.pop(pid)

    new = {pid: s for pid, s in discovered_sessions.items() if pid not in sessions}
    for pid, session in new.items():
        name = session.Process and session.Process.name()
        print(f"TODO: register callback for {name}")
        sessions[pid] = session

    print(f"Found {len(sessions)} sessions")
    for session in sessions.values():
        status = "active" if session.State else "inactive"
        print(f"{session.Process and session.Process.name()} is {status}")

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
        unregister_callbacks(sessions.values())
