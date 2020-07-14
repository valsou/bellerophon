#!/usr/bin/env python
"""Bellerophon is a companion for Pegasus-frontend application.

Bellerophon generate metadata.txt files accordingly to games
and gamelist.xml files. It also backup any asset that is not used.
"""

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import toml


# BELLEROPHON

# Constants
BASE_PATH = Path.cwd()
CONFIG_PATH = BASE_PATH / 'bellerophon.conf'
BASE_FOLDERS = [
        x.name for x
        in BASE_PATH.iterdir()
        if x.is_dir()]
MEDIA_EXT = [
    'jpg',
    'jpeg',
    'png',
    'mp4',
    'webm',
    'mp4',
    'avi',
    'mp3',
    'ogg',
    'wav'
]
SETTINGS = [
    'collection',
    'shortname',
    'extension',
    'core',
    'launch',
    'sort-by'
]


def init_config(configuration_path):
    configuration = {}
    config_file = toml.load(configuration_path)
    systems_unavailable = []
    systems_available = {}

    # Bellerophon settings
    clean_media = (
        bool(config_file["global"]["clean_media"])
        if "clean_media" in config_file["global"].keys()
        else False)
    collections_to_clean = (
        config_file["global"]["collections_to_clean"]
        if "collections_to_clean" in config_file["global"].keys()
        else False)
    master_data = (
        bool(config_file["global"]["master_data"])
        if "master_data" in config_file["global"].keys()
        else False)

    def sanitize_settings(key, value):
        if key == "extension":
            return [x.strip() for x in value.split(',')]
        return value

    # Systems settings
    for folder in config_file['systems'].keys():

        if folder in BASE_FOLDERS:

            data = {
                x: sanitize_settings(x, config_file['systems'][folder][x])
                for x
                in config_file['systems'][folder]
                if x in SETTINGS}

            data.update({"directory": folder})

            if "launch" not in data and "core" in data:
                launch = config_file['global']['launch'].replace(
                        "<CORE_VARIABLE>", data['core']).replace(
                            "<SYSTEM_VARIABLE>", folder)
                data.update({"launch": launch})
                data.pop("core", None)

            item = {
                folder: {}
            }

            item[folder].update(data)

            # Available systems
            systems_available.update(item)
        else:
            # Unavailable systems
            systems_unavailable.append(folder)

    configuration.update({
        "bellerophon": {
            "clean_media": clean_media,
            "collections_to_clean": collections_to_clean,
            "master_data": master_data
        },
        "systems": {
            "available": systems_available,
            "unavailable": systems_unavailable
        }
    })

    return configuration


def parse_gamelist(file):

    def instance_node(node, extra=None):
        if node is not None and node.text is not None:

            if not extra:
                return node.text

            if extra == "release":
                release = datetime.strptime(node.text, '%Y%m%dT%H%M%S')
                return release.strftime('%Y-%m-%d')

            if extra == "players":
                number = str(node.text).split('-')
                players = '1'
                if len(number) > 1:
                    players = number[1]
                return players

            if extra == "rating":
                percentage = float(node.text) * 100
                rating = str(int(percentage)) + '%'
                return rating

        return None

    tree = ET.parse(file)
    root = tree.getroot()
    games_dict = {}
    last_game = [0, ""]

    for game in root.findall('game'):

        if 'id' in game.attrib:
            gameid = int(game.attrib['id'])
        else:
            gameid = 0

        gamepath = [instance_node(game.find('path'))]

        gamename = Path(gamepath[0]).stem

        # Manage multiple CD games
        # Based on Skraper game id
        if gameid != 0 and gameid == last_game[0] and bool(games_dict):
            path = games_dict[last_game[1]]["file"]
            gamepath[0:0] = path
            del games_dict[last_game[1]]

        games_dict.update({
            gamename: {
                "game": instance_node(game.find('name')),
                "file": gamepath,
                "developer": instance_node(game.find('developer')),
                "publisher": instance_node(game.find('publisher')),
                "genre": instance_node(game.find('genre')),
                "description": instance_node(game.find('desc')),
                "release": instance_node(game.find('releasedate'), "release"),
                "players": instance_node(game.find('players'), "players"),
                "rating": instance_node(game.find('rating'), "rating")
            }
        })

        # To remove unused information of metadata, otherwise Pegasus will throw warnings
        games_dict[gamename] = {k: v for k, v in games_dict[gamename].items() if v is not None}

        last_game = [gameid, gamename]

    return games_dict


def get_games(systems):
    games_in_folders = {}
    systems_in_config = systems.keys()

    for folder in systems_in_config:

        if folder in BASE_FOLDERS:
            current_path = BASE_PATH/folder
            games_suffix = systems[folder]['extension']
            games = [
                x.stem for x
                in current_path.iterdir()
                if x.is_file() and str(x.suffix)[1:] in games_suffix]
            games_in_folders.update({
                str(folder): games
            })

    return games_in_folders


def get_media(systems):
    media_in_folders = {}
    systems_in_config = systems.keys()

    def sort_media(media):
        sorted_media = {}

        for key, value in sorted(media.items()):
            sorted_media.setdefault(value, {}).update({key.parent.name: key})

        return sorted_media

    for system in systems_in_config:
        media_path = Path(BASE_PATH/system/'media')
        media = {
            x: x.stem for x
            in media_path.rglob('*')
            if x.suffix[1:] in MEDIA_EXT}
        sorted_media = sort_media(media)
        media_in_folders.update({
            system: sorted_media
        })

    return media_in_folders


def generate_data(systems, games, media):

    data = {}

    for system in systems.keys():

        gamelist_path = BASE_PATH / system / 'gamelist.xml'

        if gamelist_path.is_file():
            # data.update({
            #     gamelist_path.parent.name: parse_gamelist(gamelist_path)})
            # Parse gamelist.xml
            gamelist = parse_gamelist(gamelist_path)

            # Keep only existing games in folders
            games_kept = {k: v for k, v in gamelist.items() if k in games[system]}

            # Add media field to each game
            for game in games_kept:
                if game in media[system]:
                    games_kept[game].update({"media": media[system][game]})

            data.update({
                system: {
                    "settings": systems.get(system),
                    "games": games_kept
                }
            })

        else:
            parent_folder = gamelist_path.parent.name
            print(
                f"  . . > {parent_folder}/gamelist.xml...",
                end="     ")
            print("[ Not found ]")

    if not data:
        raise ValueError("[ No System Found ]")

    return data


def create_metadata(data, master):

    master_data = []

    for system in data.keys():
        print(
            f"  . . > Creating {system}/metadata.txt...",
            end="     ")

        metadata = []
        games_count = 0

        # Generate settings header
        for key, setting in data[system]["settings"].items():
            if isinstance(setting, list):
                setting = ','.join(setting)
            line = line_master = f"{key}: {setting}\n"

            if key == "directory":
                line = ""

            if key == "extension":
                line_master = ""

            metadata.append(line)
            if master:
                master_data.append(line_master)

        metadata.append("\n")
        master_data.append("\n")

        for key, game in data[system]["games"].items():

            for field, value in game.items():

                line = line_master = f"{field}: {value}\n"

                if field == "file":
                    files = [f"\n  {x}" for x in value]
                    files_master = [f"\n  ./{system}{x[1:]}" for x in value]
                    line = f"{field}:{''.join(files)}\n"
                    line_master = f"{field}:{''.join(files_master)}\n"

                if field == "media":
                    line = "".join(f"assets.{k}: ./media/{k}/{v.name}\n" for k, v in value.items())
                    line_master = "".join(f"assets.{k}: ./{system}/media/{k}/{v.name}\n" for k, v in value.items())

                metadata.append(line)
                master_data.append(line_master)

            metadata.append("\n")
            master_data.append("\n")
            games_count += 1

        with open(BASE_PATH/system/'metadata.txt', 'w+', encoding='utf-8') as file:
            for line in metadata:
                file.write(line)

        print(f"[ Done ] [ {games_count} games written ]")

    if master:
        print(
            "  . . > Creating ./metadata.txt... (e.g. master metadata.txt)",
            end="     ")
        with open(BASE_PATH/'metadata.txt', 'w+', encoding='utf-8') as master_file:
            for line in master_data:
                master_file.write(line)
        print("[ Done ]")


def backup_media(collections_to_clean, games, media):

    backed_up = 0
    collections = (
        collections_to_clean
        if collections_to_clean is not False
        else games.keys())

    for system in collections:

        for key, value in media[system].items():

            if key not in games[system]:
                backup_dir = BASE_PATH / system / 'media.backup'

                if backup_dir.is_dir() is False:
                    Path.mkdir(backup_dir)

                for asset, item in value.items():
                    item_name = item.name
                    asset_dir = backup_dir / asset

                    if asset_dir.is_dir() is False:
                        Path.mkdir(asset_dir)

                    source_backup = f"{asset}/{item_name}"
                    to_backup = asset_dir/item_name

                    try:
                        item.rename(to_backup)
                        backed_up += 1
                    except Exception:
                        print(f"  . . > [{system}] -> {source_backup}...", end="     ")
                        print("[ Error ]")

    if backed_up > 0:
        return f"[ {backed_up} assets backed up ]"
    else:
        return "[ Nothing to back up ]"


def main():

    # Configuration file
    # input : bellerophon.conf path
    # output : (dict) of global and per system settings
    try:
        print("  > Checking configuration file...", end="     ")
        configuration = init_config(CONFIG_PATH)
        print("[ Done ]")
    except FileNotFoundError:
        raise ValueError("[ File Not Found ]")
    except Exception as err:
        raise ValueError(err)

    print(flush=True)

    games = get_games(configuration['systems']['available'])
    media = get_media(configuration['systems']['available'])

    # Generate data
    try:
        print("  > Generating data...", end="     ")
        data = generate_data(
            configuration['systems']['available'],
            games,
            media)
        print("[ Done ]")
    except ValueError as err:
        raise ValueError(err)
    except Exception:
        raise ValueError("[ Unknown Error ]")

    print(flush=True)

    # Create metadata files
    try:
        print("  > Creating metadata files...")
        create_metadata(
            data,
            configuration["bellerophon"]["master_data"])
    except Exception as err:
        raise ValueError(err)

    print(flush=True)

    if configuration["bellerophon"]["clean_media"]:
        # Backup unused media files
        try:
            print("  > Checking unused media files...", end="     ")
            backup = backup_media(
                configuration["bellerophon"]["collections_to_clean"],
                games,
                media)
            print(backup)

        except Exception as err:
            raise ValueError(err)

    print(flush=True)

    # for not_found_system in configuration['systems']['available']:
    # print(f"Not found systems : {', '.join(configuration['systems']['unavailable'])}")
    print(f"  [!] Not found systems : {', '.join(configuration['systems']['unavailable'])}")


if __name__ == "__main__":
    start = datetime.now()
    BEGIN_MESSAGE = '''
  ≠------------------------------------------------≠
  ¦    * . BELLEROPHON * . *                       ¦
  ¦                                                ¦
  ¦              - a Pegasus-frontend companion    ¦
  ≠------------------------------------------------≠
  '''
    print(BEGIN_MESSAGE)

    try:
        main()
    except ValueError as err:
        print(err)

    finish = datetime.now()
    END_MESSAGE = f'''
  [ Bellerophon took {round((finish-start).total_seconds(),2)} s ]

  Hope the script was helpful. . * * . . . * . * * . .
    '''
    print(END_MESSAGE)
    input("")
