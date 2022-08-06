import sched
import time
from typing import Dict, List, Iterable

import spotipy
from comtypes import COMError
from pycaw.callbacks import AudioSessionEvents
from pycaw.utils import AudioSession, AudioUtilities
from spotipy.oauth2 import SpotifyOAuth

foreground_process_names = ["chrome.exe", "firefox.exe"]
sessions: Dict[int, AudioSession] = {}


def _unregister_callbacks(sessions: Iterable[AudioSession]):
    for s in sessions:
        s.unregister_notification()
        print(f"Unregistered callback for {s.Process and s.Process.name()}")


class AudioStateCallback(AudioSessionEvents):
    """Audio Session Callback which keeps track of previous state and process name.
    It registers itself automatically with the session passed to the constructor.
    """

    def __init__(self, session: AudioSession) -> None:
        super().__init__()
        assert session.Process
        self.session = session
        self.process_name: str = session.Process.name()
        self.state: str = self.AudioSessionState[session.State]
        session.register_notification(self)
        print(f"Registered callback for {self.process_name}")

    def on_state_changed(self, new_state, new_state_id):
        if new_state == "Active":
            self.on_active()
        elif new_state == "Inactive":
            self.on_inactive()
        elif new_state == "Expired":
            self.on_expired()
        else:
            print("Warning: unknown state:", new_state)
        self.state = new_state

    def on_active(self):
        pass

    def on_inactive(self):
        pass

    def on_expired(self):
        pass


from interlude.spotify import SpotifyState, SpotifyClient


class PauseSpotifyCallback(AudioStateCallback):
    active_session_count = 0
    spotify_state = 0

    def __init__(self, session: AudioSession) -> None:
        super().__init__(session)
        self.client = SpotifyClient()
        if self.state == "Active":
            self.active_session_count += 1

    def on_active(self):
        self.active_session_count += 1
        if self.active_session_count > 1:
            return  # there was already some foreground sound, nothing to do

        # First foreground source was just activated
        # check if we should put the player on hold
        self.client._get_playback()  # Refresh player state in case user paused
        if self.client.state == SpotifyState.playing:
            self.client.put_on_hold()

    def on_inactive(self):
        self.active_session_count -= 1
        if self.active_session_count > 0:
            return  # there is still foreground sound, nothing to do

        # Foreground sound ceased, resume playback if it was on hold
        self.client._get_playback()
        if self.client.state == SpotifyState.hold:
            self.client.resume_from_hold()

    def on_expired(self):
        if self.state == "Active":
            self.active_session_count -= 1

        if self.active_session_count > 0:
            return  # there is still foreground sound, nothing to do

        # Foreground sound ceased, resume playback if it was on hold
        self.client._get_playback()
        if self.client.state == SpotifyState.hold:
            self.client.resume_from_hold()
        # TODO: avoid code duplication


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
        PauseSpotifyCallback(session)
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
