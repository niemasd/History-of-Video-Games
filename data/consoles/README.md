This directory contains all video game consoles, which are organized into sub-folders based on company. The following attributes are required:

* **`name`** — The English name of the console as a string
* **`date_start`** — The release date(s) of the console as a dictionary where keys are region names as strings and values are dates as strings in the format `YYYY-MM-DD`

The following attributes are optional:

* **`image`** — The path to an image of the console as a string (place images in [`data/images`](../images))
* **`date_end`** — The discontinue date(s) of the console as a dictionary where keys are region names as strings and values are dates as strings in the format `YYYY-MM-DD`
