""" Customise the pycaw AudioSession event callback, logic to keep track of audio sessions"""
import logging
import sched
from typing import Dict, Iterable, List, Type

from comtypes import COMError
from pycaw.callbacks import AudioSessionEvents
from pycaw.utils import AudioSession, AudioUtilities


class AudioStateCallback(AudioSessionEvents):
    """Audio Session Callback which keeps track of previous state and process name.
    It registers itself automatically with the session passed to the constructor.
    """

    def __init__(self, session: AudioSession, **kwargs) -> None:
        super().__init__()
        assert session.Process
        self.session = session
        self.process_name: str = session.Process.name()
        self.state: str = self.AudioSessionState[session.State]
        session.register_notification(self)
        logging.info(f"Registered callback for {self.process_name}")
        if kwargs:
            logging.warning(f"Unused named arguments: {kwargs}")

    def on_state_changed(self, new_state, new_state_id):
        """Expose individual state changes as interface functions"""
        if new_state == "Active":
            self.on_active()
        elif new_state == "Inactive":
            self.on_inactive()
        elif new_state == "Expired":
            self.on_expired()
        else:
            logging.warning("Warning: unknown state:", new_state)
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
        logging.info(f"Unregistered callback for {s.Process and s.Process.name()}")


def discover_foreground_sessions(
    sessions: Dict[int, AudioSession],
    Callback: Type[AudioStateCallback],
    foreground_process_names: List[str],
    **kwargs,
) -> Dict[int, AudioSession]:
    """Find all audio sessions of foreground registered apps.
    Kwargs are passed to the Callback if new audio session is discovered."""
    try:
        all_discovered: List[AudioSession] = AudioUtilities.GetAllSessions()
    except COMError:
        logging.error("No audio output device registered!")
        return {}
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
        Callback(session=session, **kwargs)
        sessions[pid] = session

    return sessions
