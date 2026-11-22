# The Picture That Tastes of One Ingredient

[![Competition](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![Rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Azet17/makefun-the-picture-that-tastes-of-one-20261122-2047/rank.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![Reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Azet17/makefun-the-picture-that-tastes-of-one-20261122-2047/reward.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)

One delicious thing, rendered to make you hungry: a steaming bowl of ramen,
three-quarter view — glossy amber broth, springy noodles, a halved soft-boiled
egg with a jammy orange yolk, glistening chashu, scallions, chili-oil sheen,
chopsticks lifting noodles, wisps of steam, on a warm dark wooden table.

## How it works

`main.py` is Python 3.13 standard library only — no PIL, no numpy, no fonts,
no network. It draws the scene procedurally into a 2048x2048 buffer
(supersampled 2x), downsamples to 1024x1024, applies a vignette and subtle
grain, and encodes the PNG by hand with `zlib` + `struct`. Output is fully
deterministic (fixed seed).

## Run

```sh
python3 main.py   # writes /output/entry.png (1024x1024 PNG)
```

## License

MIT — see [LICENSE](LICENSE).
