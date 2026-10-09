"""
Clash Clone -- singleplayer Clash-Royale-style game.

Run from the repo root with:   python src/main.py
(or from inside src/ with:      python main.py)
"""

import os
import sys

# make sure sibling modules import whether run from repo root or src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Game


def main():
    Game().run()


if __name__ == "__main__":
    main()
