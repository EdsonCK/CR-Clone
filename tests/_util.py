"""
Shared setup for the tests: imported first by every test script.

  * headless pygame (no window, no sound card needed)
  * src/ on the import path, the game folder as the working directory
  * a throw-away save folder (CLASH_CLONE_SAVE_DIR), so tests never touch
    your real profile - it's deleted when the test ends
"""

import atexit
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
TMP = tempfile.mkdtemp(prefix="clash_clone_test_")
os.environ["CLASH_CLONE_SAVE_DIR"] = TMP
atexit.register(shutil.rmtree, TMP, True)
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(ROOT)
