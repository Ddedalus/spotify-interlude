from numpy import choose
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import time


def strip_markets(response):
    if isinstance(response, dict):
        for key in response.keys():
            if key == "available_markets":
                response[key] = []
            else:
                response[key] = strip_markets(response[key])
    elif isinstance(response, list):
        return [strip_markets(r) for r in response]

    return response


def print_playback(playback):
    print(
        "Playing:" if playback["is_playing"] else "Paused:",
        playback["item"]["name"],
        "by",
        playback["item"]["artists"][0]["name"],
    )


def get_device():
    """ Get currently active device or the Surface laptop"""
    devices = sp.devices()["devices"]
    preferences = [d for d in devices if d["is_active"]] + [
        d for d in devices if d["name"] == "SURFACE"
    ]
    try:
        return preferences[0]
    except IndexError:
        raise ValueError("No suitable device found")


if __name__ == "__main__":
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id="b28755671fa94530b587e9b8c30d1951",
            client_secret="95bb66edd73842cdb2b925bf43eb11a9",
            redirect_uri="http://localhost:9090",
            scope=["user-modify-playback-state", "user-read-playback-state"],
        )
    )
    device = get_device()

    playback = sp.current_playback()

    if playback and playback["is_playing"]:
        print("Enough of that music!")
        sp.pause_playback(device_id=playback["device"]["id"])
    else:
        print("Let's play some music!")
        sp.start_playback(device_id=device["id"])

    time.sleep(0.5)
    playback = sp.current_playback()
    print_playback(playback)

