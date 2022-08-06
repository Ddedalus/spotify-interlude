from ast import Call
from pycaw.callbacks import AudioSessionEvents
from typing import Dict, List, Iterable, Type
from pycaw.utils import AudioSession, AudioUtilities
from comtypes import COMError
import sched

foreground_process_names = ["chrome.exe", "firefox.exe"]


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
        """Expose individual state changes as interface functions"""
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
        """Called when the audio session becomes active"""
        pass

    def on_inactive(self):
        """Called when the audio session becomes inactive"""
        pass

    def on_expired(self):
        """Called when the audio session expires"""
        pass


def unregister_callbacks(sessions: Iterable[AudioSession]):
    for s in sessions:
        s.unregister_notification()
        print(f"Unregistered callback for {s.Process and s.Process.name()}")


def discover_foreground_sessions(
    scheduler: sched.scheduler,
    sessions: Dict[int, AudioSession],
    Callback: Type[AudioStateCallback],
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
        Callback(session)
        sessions[pid] = session

    print(f"Tracking {len(sessions)} audio sessions")

    # check again in a moment
    scheduler.enter(3, 5, discover_foreground_sessions, (scheduler, sessions, Callback))
