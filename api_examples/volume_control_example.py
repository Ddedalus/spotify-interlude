"""
Enter the right 'app_name' and play something to initiate a WASAPI session.
Then launch this file ;)
Requirements: Python >= 3.6 - f strings ;)
following "IAudioSessionEvents" callbacks are supported:
:: Gets called on volume and mute change:
IAudioSessionEvents.OnSimpleVolumeChanged()
-> on_simple_volume_changed()
:: Gets called on session state change (active/inactive/expired):
IAudioSessionEvents.OnStateChanged()
-> on_state_changed()
:: Gets called on for example Speaker unplug
IAudioSessionEvents.OnSessionDisconnected()
-> on_session_disconnected()
https://docs.microsoft.com/en-us/windows/win32/api/audiopolicy/nn-audiopolicy-iaudiosessionevents
"""
import time

from comtypes import COMError
from pycaw.callbacks import AudioSessionEvents
from pycaw.utils import AudioUtilities

foreground_apps = ["chrome.exe", "firefox.exe"]


class StateLoggingCallback(AudioSessionEvents):
    def __init__(self, process_name: str = "") -> None:
        super().__init__()
        self.process_name = process_name

    def on_state_changed(self, new_state, new_state_id):
        print(f"{self.process_name} changed state to {new_state}")

    def on_session_disconnected(self, disconnect_reason, disconnect_reason_id):
        print(
            f"{self.process_name} session was disconnected because {disconnect_reason}"
        )


def add_callbacks():
    try:
        sessions = AudioUtilities.GetAllSessions()
    except COMError:
        exit("No speaker set up")

    for session in sessions:
        if session.Process and session.Process.name() in foreground_apps:
            callback = StateLoggingCallback(process_name=session.Process.name())
            session.register_notification(callback)
            print(f"Registered callback for {session.Process.name()}")

    try:
        # wait 300 seconds for callbacks
        time.sleep(300)
    except KeyboardInterrupt:
        pass
    finally:

        # unregister callback(s)
        # unregister_notification()
        # (only if it was also registered.)
        # pycaw.utils -> unregister_notification()
        for session in sessions:
            session.unregister_notification()


if __name__ == "__main__":
    add_callbacks()
