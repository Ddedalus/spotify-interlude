# https://stackoverflow.com/questions/60943757/create-a-shortcut-lnk-of-file-in-windows-with-python3

from win32com.client import Dispatch
from pathlib import Path
import sys

repo_root = Path(__file__).parent.parent.resolve()

shell = Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(r"Interlude.lnk")

shortcut.Targetpath = sys.executable
shortcut.Arguments = r"api_examples/hello.py"
shortcut.WorkingDirectory = str(repo_root)
shortcut.Description = "Interlude: pause Spotify during audio calls"
shortcut.WindowStyle = 7

shortcut.save()
