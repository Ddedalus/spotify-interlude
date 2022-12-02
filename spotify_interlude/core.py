""" Core logic to trigger Spotify state changes in reponse to audio session state changes."""
import logging
import sched
from typing import Dict, List

from pycaw.utils import AudioSession

from spotify_interlude.audio_session import (
    AudioStateCallback,
    discover_foreground_sessions,
)
from spotify_interlude.spotify import SpotifyClient, SpotifyState


class PauseSpotifyCallback(AudioStateCallback):
    """Callback to put Spotify playback on hold when audio sessions are active"""

    scheduler: sched.scheduler
    client: SpotifyClient
    active_session_count = 0
    warmup_duration: float = 2.0

    def __init__(self, session: AudioSession) -> None:
        super().__init__(session)
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
                logging.info("Deleting a warmup event")
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
            self.scheduler.enter(self.warmup_duration, 10, self.client.resume_playback)
        else:
            logging.warning(f"Tried to activate playback in state {self.client.state}")


def manage_sessions_task(
    scheduler: sched.scheduler,
    interval: float,
    process_names: List[str],
    sessions: Dict[int, AudioSession] = {},
):
    """Periodic task updating a collection of active audio sessions."""
    sessions = discover_foreground_sessions(
        sessions, PauseSpotifyCallback, process_names
    )
    scheduler.enter(
        interval,
        5,
        manage_sessions_task,
        (scheduler, interval, process_names, sessions),
    )
    return sessions
