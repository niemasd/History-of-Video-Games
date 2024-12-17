---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(welcome)=
# Welcome!

```{note}
Source Code: [`history_video_games/intro.md`](https://github.com/niemasd/History-of-Video-Games/blob/main/history_video_games/intro.md)
```

Welcome to *History of Video Games*!
This is an Open Educational Resource (OER) about the history of video games.

```{code-cell} ipython3
:tags: ["remove-input"]
from datetime import datetime
from pytz import timezone
print("Built: %s" % datetime.now(timezone("America/Los_Angeles")).strftime("%B %-d, %Y at %-I:%M %p %Z"))
```

The most recent version of this resource can be found as a [website](https://niema.net/History-of-Video-Games)
or [PDF](https://github.com/niemasd/History-of-Video-Games/releases/latest/download/History-of-Video-Games.pdf).
