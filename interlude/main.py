import sched
from typing import Dict

from pycaw.utils import AudioSession

from interlude.spotify import SpotifyState, SpotifyClient
from interlude.audio_session import (
    AudioStateCallback,
    unregister_callbacks,
    discover_foreground_sessions,
)

sessions: Dict[int, AudioSession] = {}
scheduler = sched.scheduler()


class PauseSpotifyCallback(AudioStateCallback):
    active_session_count = 0
    spotify_state = 0
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


if __name__ == "__main__":
    try:
        scheduler.enter(
            0,
            5,
            discover_foreground_sessions,
            (scheduler, sessions, PauseSpotifyCallback),
        )
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, cleaning up...")
    finally:
        unregister_callbacks(sessions.values())
