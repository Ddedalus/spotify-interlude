""" Deal with Spotify API authentication and define Spotify state management."""
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyState(str, Enum):
    """State of the Spotify player.
    playing: the music is playing
    hold: music was paused because of foreground sound and can be resumed
    warmup: the foreground sound is over, player will resume after a delay
    paused: music was paused by the user
    off: no client capable of playing music found
    """

    playing = "playing"
    hold = "hold"
    warmup = "warmup"
    paused = "paused"
    off = "off"


class SpotifyClient:
    def __init__(
        self, client_id: str, secret: str, target_device_names: List[str] = []
    ) -> None:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=secret,
            redirect_uri="http://localhost:9090",
            scope=["user-modify-playback-state", "user-read-playback-state"],
        )
        self.target_device_names = target_device_names
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.state: SpotifyState = SpotifyState.off

    def hold_playback(self):
        """Pause Spotify playback because of foreground audio."""
        if self.state == SpotifyState.warmup:
            self.state = SpotifyState.hold
            return
        assert (
            self.state == SpotifyState.playing
        ), "Can only hold from playing or warmup"
        try:
            device = self._get_device()
        except:
            logging.info("It seems the device was killed in the meantime")
            return
        self.sp.pause_playback(device_id=device["id"])
        self.state = SpotifyState.hold
        logging.info("Playback on hold")

    def warmup(self):
        """Start the warmup period"""
        self.state = SpotifyState.warmup
        logging.info("Warmup...")

    def resume_playback(self):
        """Resume Spotify playback once foreground audio finishes."""
        assert (
            self.state == SpotifyState.warmup
        ), "Can only resume after a warmup period!"
        try:
            device = self._get_device()
        except ValueError:
            logging.warning("No device found that could resume playback")
            self.state = SpotifyState.off
            return

        self.sp.start_playback(device_id=device["id"])
        self.state = SpotifyState.playing
        logging.info("Resumed playback")

    def _get_device(self) -> Dict[str, Any]:
        """Get currently active device or one of the preferred ones by name."""
        try:
            devices = self.sp.devices()["devices"]
        except Exception as e:
            logging.error(e)
            self.state = SpotifyState.off
            raise ValueError("No suitable device found")

        preferences = [d for d in devices if d["is_active"]] + [
            d for d in devices if d["name"] in self.target_device_names
        ]
        try:
            device = preferences[0]
        except IndexError:
            self.state = SpotifyState.off
            raise ValueError("No suitable device found")
        if self.state == SpotifyState.off:
            # New device found, update the state
            self.state = SpotifyState.playing
            self._get_playback()
        return device

    def _get_playback(self) -> Optional[Dict[str, Any]]:
        """Refresh the state of Spotify playback and update the state"""
        playback = self.sp.current_playback()
        if playback and playback["is_playing"]:
            # Can't deny the facts!
            self.state = SpotifyState.playing
        elif self.state == SpotifyState.playing:
            # User manually pressed the pause button
            self.state = SpotifyState.paused
        # The state doesn't change if it's hold, warmup or off
        return playback
