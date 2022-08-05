"""
Mutes the volume of all processes, but unmutes chrome.exe process.
"""
from multiprocessing.dummy import Process
from unicodedata import name
from pycaw.pycaw import AudioUtilities, AudioSession
from pycaw.api.audioclient import ISimpleAudioVolume
from pycaw.api.endpointvolume import IAudioEndpointVolume
from typing import List

if __name__ == "__main__":
    sessions: List[AudioSession] = AudioUtilities.GetAllSessions()

    for session in sessions:
        volume: ISimpleAudioVolume = session.SimpleAudioVolume
        print()
        print("Process:", session.Process)
        print("State", session.State)
        if session.Process:
            print("Process name:", session.Process.name())
