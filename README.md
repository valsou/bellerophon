# bellerophon
          - a Pegasus-frontend companion

The idea is : **multiple** folders full of games, **multiple** gamelist.xml (EmulationStation) files, **1** configuration file to determine global/per system preferences.
And one Bellerophon to kick the ass of the chimera.

## Changelog

- version 0.16 (06/07/2020) :
	+ no more <PATH_VARIABLE> in .conf
	+ added <CORE_VARIABLE> and <SYSTEM_VARIABLE> instead.

- version 0.15 (06/07/2020) :
	+ Big refactoring to reach a Pylint note >9
	+ Change of behavior for `path` parameter in `bellerophon.conf`. Please update your file accordingly.
	Now `path` value is concatenated inside `launch` parameter (Retroarch) via `<PATH_VARIABLE>` keyword

- version 0.1 (05/07/2020) :
	+ Initialization of the project

## Pegasus-frontend
[ https://pegasus-frontend.org ] or [ https://github.com/mmatyas/pegasus-frontend ]

Pegasus is a front-end to navigate in your games library. It relies on metadata.txt files that contain all data about games, paths and assets.

## What does Bellerophon ?
Bellerophon is a Python script to :
- generate metadata files
- clean media library (unused assets). No need of the gamelist.xml for that.

## Improvements and ideas
- scrape directly via Bellerophon ? (maybe not...)
- permit to take as *database* something else than gamelist.xml (EmulationStation) files
- improve the .conf file to be compatible with all features proposed by Pegasus frontend (ignore files, regexes, sorting...)
- be compatible with other folder structures (another name than `media`, names of games as folders names, etc.)
- a GUI/CLI to choose what to do (e.g. just clean the media, just generate metadata files)

## Requirements
Python >= 3.6

toml >= 0.10.1

You can type : `pip install requirements.txt`

In order to work the script also needs :

- one `gamelist.xml` file in each system folder
- assets folder named `media` in each system foler

If `gamelist.xml` is not found, the `metadata.txt` won't be created.

**So scrape your games and ask your software to output a gamelist.xml.**

**Skraper (Screen-scraper) does that very well. :)**

[ https://www.skraper.net ]

### Please, backup your `metadata.txt` files before running the script.
### The script overwrite all `metadata.txt` for systems listed in `bellerophon.conf` and move unused assets in `media.backup` folder if necessary.
### Nothing is removed.

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




## Disclaimer
The script has been made for my use case but i tried to develop it with other needs in mind.
I personnaly don't use custom collections (e.g. "Platform games", "Best games for kids", etc.) so it may not work in thoses cases.
