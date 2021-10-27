<img src="images/logo_bellerophon.svg" width="60%" title="bellérophon, a pegasus-frontend companion" />

The idea is : **multiple** folders full of games, **multiple** gamelist.xml (EmulationStation) files, **1** configuration file to determine global/per system preferences.
And one Bellerophon to kick the ass of the chimera.

> For now i test and develop the script for my own use-case, e.g : Pegasus-frontend + Shield TV (Android), one `collection` (system) per metadata.txt
If you want it to work for your need, or simply work (because there is a bug that i have not seen), do not hesitate to let me know. Thank you. :)

## Quick tutorial video
https://www.youtube.com/watch?v=Jhuww7Jl6N0

## Pegasus-frontend
[ https://pegasus-frontend.org ] or [ https://github.com/mmatyas/pegasus-frontend ]

Pegasus is a front-end to navigate in your games library. It relies on metadata.txt files that contain all data about games, paths and assets.

## What does Bellerophon ?
Bellerophon is a Python script to :
- generate metadata files
- clean media library (unused assets). No need of the gamelist.xml for that.

## Requirements
toml >= 0.10.1

Install or upgrade pip : https://pip.pypa.io/en/stable/installing/#upgrading-pip

Module to install (TOML) : https://pypi.org/project/toml/

You can type : `pip install requirements.txt`

Or : `py -m pip install toml`

Developed in a Python 3.6 environment.

In order to work the script also needs :

- one `gamelist.xml` file in each system folder
- assets folder named `media` in each system foler

If `gamelist.xml` is not found, the `metadata.txt` won't be created.

**So scrape your games and ask your software to output a gamelist.xml.**

**Skraper (Screen-scraper) does that very well. :)**
[ https://www.skraper.net ]

### Please, backup your `metadata.txt` files before running the script if you're not sure what your are doing. `metadata.txt` output is overwritten each time, `gamelist.xml` is read-only.

## Usage
### Gamelist.xml
Scrape your games with Skraper (or another scraper that output an EmulationStation gamelist.xml [not tested]).
Ask for the right media folders names (they will be used as is).

### Bellerophon
1. Download `bellerophon.py` and `bellerophon.sample.conf` at the root of your library. Below the tree of my own library :

```
NVIDIA_SHIELD/
├─ bellerophon.py
├─ bellerophon.conf
└─ arcade/
    ├─ game1.zip
    ├─ game2.zip
    ├─ game3.zip
    ├─ gamelist.xml
    └─ media/
        ├─ wheel/
        |   ├─ game1.png
        |   ├─ game2.png
        |   └─ game3.png
        └─ screenshot/
            ├─ game1.png
            ├─ game2.png
            └─ game3.png
```

2. Rename `bellerophon.sample.conf` to `bellerophon.conf`
3. Edit `bellerophon.conf` according to your needs.

Add all your systems configurations. The script will skip configuration of a non existing folder/system.

4. On Desktop double-clic `bellerophon.py`.
On CLI type `py bellerophon.py`.

## bellerophon.conf
The config file consists of a global variable (for now juste the Retroarch command), and systems variables.

### global
|key|type|value|
|---|---|---|
|launch | string | A multiline command for Retroarch (Android). Edit the command to your need for Windows/Unix OS.|

### systems
#### systems.<SYSTEM_DIRECTORY_NAME>
|key|type|value|
|---|---|---|
|shortname | string | *An optional short name for the collection, often an abbreviation (like MAME, NES, etc.). Should be lowercase.* (official  documentation) |
|collection | string | *Creates a new collection with the value as name. **This is a required field.*** (official  documentation) |
|extension | string | *A comma-separated list of file extensions (without the . dot), or a list of such lines. All files with these extensions will be included.* (official  documentation) Will be a list in the future. |
|core *optional* | string | Libretro core name with *.so* extension. It will be concatenated in each metadata files. |
|launch *optional* | string | A launch command that will override the default one. So the core variable will not be used. |

## Changelog
- 18/12/2020
    + Fix master data. Now a "master" folder is created with a `metadata.txt` inside. Use that one.
- 23/09/2020
	+ Fix description with indent and linebreaks
	+ Fix bellerophon.sample.conf who had "collection" line under "shortname" line (that order doesn't work !)

- 12/07/2020
    	+ Big refactoring
    	+ Add counter to see number of games written in metadata.txt
    	+ Add "sort-by" system setting for bellerophon.conf -> see Pegasus documentation
    	+ Add "clean_media" global setting for bellerophon.conf -> check unused assets or not
    	+ Add "collections_to_clean" global setting for bellerophon.conf -> list of collections that you want to check (if None, all collections will be checked)
    	+ Add "master_data" global setting for bellerophon.conf -> create a metadta.txt at the root (that's a merge of all metadata.txt)

- 05/07/2020
	+ Initialization of the project
