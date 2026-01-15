This directory contains all video game consoles, which are organized into sub-folders based on company. The following attributes are required:

* **`name`** — The English name of the console as a string
* **`date_start`** — The release date(s) of the console as a dictionary where keys are region names as strings and values are dates as strings in the format `YYYY-MM-DD`

The following attributes are optional:

* **`name_orig`** — The original name of the console (e.g. in its original language) as a string
* **`variant_of`** — If this console is a variant of another console, the English name of that other console as a string
* **`photo`** — The path to a photo of the console as a string (place images in [`data/images`](../images))
* **`date_end`** — The discontinue date(s) of the console as a dictionary where keys are region names as strings and values are dates as strings in the format `YYYY-MM-DD`
