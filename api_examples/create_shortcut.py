# https://stackoverflow.com/questions/60943757/create-a-shortcut-lnk-of-file-in-windows-with-python3

from win32com.client import Dispatch

shell = Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(r"Interlude.lnk")
shortcut.Targetpath = r"C:\Users\hbere\AppData\Local\pypoetry\Cache\virtualenvs\interlude-q_KpqPTc-py3.8/Scripts\python.EXE"
shortcut.Arguments = r"api_examples/hello.py"
shortcut.WorkingDirectory = r"C:\Users\hbere\Documents\Python\ Scripts\interlude"
shortcut.Description = "Interlude: pause Spotify during audio calls"
shortcut.save()
