# The Picture That Tastes of One Ingredient

[![Competition](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![Rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Azet17/makefun-the-picture-that-tastes-of-one-20261122-2047/rank.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![Reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Azet17/makefun-the-picture-that-tastes-of-one-20261122-2047/reward.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)

One ingredient, one craving: a steaming bowl of ramen, three-quarter view —
glossy amber broth, springy noodles, a halved soft-boiled egg with a jammy
orange yolk, glistening chashu, scallions, chili-oil sheen, chopsticks
lifting noodles, and wisps of steam over a warm dark wooden table.

## How it is made

`main.py` is Python 3 standard library only — no PIL, no numpy, no fonts,
no network. It renders the scene at 2x (2048x2048) with its own shape
drawing (ellipses, gradient broth, wavy noodle strands, alpha-blended steam
and gloss), downsamples to 1024x1024, applies a warm vignette, and encodes
the PNG itself with `zlib` + `struct`. Output is deterministic.

## Run

```sh
python3 main.py   # writes /output/entry.png (1024x1024 PNG)
```
