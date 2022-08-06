""" Core logic to trigger Spotify state changes in reponse to audio session state changes."""
import sched
from typing import Dict

from pycaw.utils import AudioSession

from interlude.audio_session import (
    AudioStateCallback,
    discover_foreground_sessions,
    unregister_callbacks,
)
from interlude.spotify import SpotifyClient, SpotifyState

scheduler = sched.scheduler()


class PauseSpotifyCallback(AudioStateCallback):
    """Callback to put Spotify playback on hold when audio sessions are active"""

    active_session_count = 0
    scheduler: sched.scheduler = scheduler

    def __init__(self, session: AudioSession) -> None:
        super().__init__(session)
        self.client = SpotifyClient()
        if self.state == "Active":
            self.active_session_count += 1

    def on_active(self):
        self.active_session_count += 1
        self.client._get_playback()  # Refresh player state in case user paused

        if self.client.state in [SpotifyState.warmup, SpotifyState.playing]:
            self.client.hold_playback()

        # Delete all pending warmup tasks from the scheduler
        for event in self.scheduler.queue:
            if event.action == self.client.resume_playback:
                print("Deleting a warmp event")
                self.scheduler.cancel(event)

    def on_inactive(self):
        self.active_session_count -= 1
        if self.active_session_count > 0:
            return  # there is still foreground sound, nothing to do

        self.activate_playback()

    def on_expired(self):
        if self.state == "Active":
            self.active_session_count -= 1

        if self.active_session_count > 0:
            return  # there is still foreground sound, nothing to do
        self.activate_playback()

    def activate_playback(self):
        # Foreground sound ceased, resume playback if it was on hold
        self.client._get_playback()
        if self.client.state == SpotifyState.hold:
            self.client.warmup()
            self.scheduler.enter(2, 10, self.client.resume_playback)
        else:
            print(f"Tried to activate playback in state {self.client.state}")


def manage_sessions_task(scheduler, sessions):
    """Periodic task updating a collection of active audio sessions."""
    sessions = discover_foreground_sessions(sessions, PauseSpotifyCallback)
    scheduler.enter(3, 5, manage_sessions_task, (scheduler, sessions))


if __name__ == "__main__":
    sessions: Dict[int, AudioSession] = {}
    scheduler.enter(0, 5, manage_sessions_task, (scheduler, sessions))
    try:
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())
