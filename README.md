# Introduction

A python program to parse a screenshot and output a text-representation of the detected
block-colours for the monolith minigame in drv3.

Currently (probably?) only works for the difficult version of the monolith game,
and it is almost certainly *necessary* that the game resolution is either
`1280x800` with letterboxing or `1280x720` without letterboxing.

Usage involves provide a path to a screenshot, or alternatively editing
the screenshot-function in the code to take a screenshot automatically if
your setup has a method for doing that (e.g. scrot on linux/X11) or perhaps
PIL's `Image.ImageGrab()` on windows.


# Usage

Usage: Edit the `game_x0, game_y0, game_xn, game_yn` variables in the first few
lines of `run.py` to match the top left and bottom right corner of the game window
(the resolution requirement still holds because of the template-images).

Afterwards, run:

```
python3 run.py examples/ex05.png
```

and a text-representation of the board will be displayed, as well as a reference image
saved to the `outputs/`-directory (but that image is not really useful for anything but
quickly verifying that nothing is terribly wrong with the classifications).

The text-representation can be passed to a solver or other program for processing the
board (neither of which are included in this repository).

