from enum import Enum
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, Any, Optional


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
    def __init__(self) -> None:
        auth_manager = SpotifyOAuth(
            client_id="b28755671fa94530b587e9b8c30d1951",
            client_secret="95bb66edd73842cdb2b925bf43eb11a9",
            redirect_uri="http://localhost:9090",
            scope=["user-modify-playback-state", "user-read-playback-state"],
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.state: SpotifyState = SpotifyState.off

    def hold_playback(self):
        """Pause Spotify playback because of foreground audio."""
        assert self.state in [
            SpotifyState.playing,
            SpotifyState.warmup,
        ], "Can only hold from playing!"
        try:
            device = self._get_device()
        except:
            print("It seems the device was killed in the meantime")
            return
        self.sp.pause_playback(device_id=device["id"])
        self.state = SpotifyState.hold

    def warmup(self):
        """Start the warmup period"""
        self.state = SpotifyState.warmup

    def resume_playback(self):
        """Resume Spotify playback once foreground audio finishes."""
        assert (
            self.state == SpotifyState.warmup
        ), "Can only resume after a warmup period!"
        try:
            device = self._get_device()
        except ValueError:
            print("No device found that could resume playback")
            self.state = SpotifyState.off
            return

        self.sp.start_playback(device_id=device["id"])
        self.state = SpotifyState.playing

    def _get_device(self) -> Dict[str, Any]:
        """Get currently active device or the Surface laptop"""
        try:
            devices = self.sp.devices()["devices"]
        except Exception as e:
            print(e)
            self.state = SpotifyState.off
            raise ValueError("No suitable device found")

        preferences = [d for d in devices if d["is_active"]] + [
            d for d in devices if d["name"] == "SURFACE"
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
