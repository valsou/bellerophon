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
# version 0.1

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

    # Systems settings
    for folder in config_file['systems'].keys():

        if folder in BASE_FOLDERS:

            data = {}

            if "collection" in config_file['systems'][folder]:
                data.update({"collection": config_file['systems'][folder]['collection']})

            if "shortname" in config_file['systems'][folder]:
                data.update({"shortname": config_file['systems'][folder]['shortname']})

            data.update({"directory": folder})

            if "extension" in config_file['systems'][folder]:
                dict_extension = config_file['systems'][folder]['extension']
                extension = [
                    x.strip() for x
                    in dict_extension.split(',')]
                data.update({"extension": extension})

            if "launch" in config_file['systems'][folder]:
                data.update({"launch": config_file['systems'][folder]['launch']})
            else:
                core = config_file['systems'][folder]['core']
                launch = config_file['global']['launch'].replace(
                        "<CORE_VARIABLE>", core).replace(
                            "<SYSTEM_VARIABLE>", folder)
                data.update({"launch": launch})

            item = {
                folder: {}
            }

            item[folder].update(data)

            # Available systems
            systems_available.update(item)

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

        gamepath = instance_node(game.find('path'))
        gamename = Path(gamepath).stem

        # Manage multiple CD games
        # Based on Skraper game id
        if gameid != 0 and gameid == last_game[0] and bool(games_dict):
            path = games_dict[last_game[1]]["file"]
            gamepath = f"{path.strip()}\n{gamepath}"
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

        last_game = [gameid, gamename]

    return games_dict


def sort_media(media):
    sorted_media = {}

    for key, value in sorted(media.items()):
        sorted_media.setdefault(value, []).append(key)

    return sorted_media


def generate_data(systems):
    data = {}
    iter = 0

    for system in systems.keys():

        if iter == 0:
            print("")

        gamelist_path = BASE_PATH / system / 'gamelist.xml'

        if gamelist_path.is_file():
            data.update({
                gamelist_path.parent.name: parse_gamelist(gamelist_path)})

        else:
            parent_folder = gamelist_path.parent.name
            print(
                f"  . . > {parent_folder}/gamelist.xml...",
                end="     ")
            print("[ Not found ]")

        iter += 1

    if not data:
        raise ValueError("[ No System Found ]")

    return data


def get_games(systems):
    games_in_folders = {}
    all_folders = [x.name for x in BASE_PATH.iterdir() if x.is_dir()]
    systems_in_config = systems.keys()

    for folder in systems_in_config:

        if folder in all_folders:
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


def create_metadata(data, games, media, parameters, master):

    master_data = []

    for system in data.keys():
        print(
            f"  . . > Creating {system}/metadata.txt...",
            end="     ")

        metadata = []

        file = open(
            BASE_PATH/system/'metadata.txt',
            'w+',
            encoding='utf-8')

        # Generate system header
        for key, value in parameters[system].items():

            if isinstance(value, list):
                value = ','.join(value)

            line = f"{key}: {value}\n"
            if key != "directory":
                metadata.append(line)

            if master and key != "extension":
                master_data.append(line)

        metadata.append("\n")
        if master:
            master_data.append("\n")

        for game in games[system]:

            if game in data[system].keys():

                if data[system][game]['game'] is not None:
                    line = f"game: {data[system][game]['game']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['file'] is not None:

                    metadata.append("file:\n")
                    for file_path in data[system][game]['file'].splitlines():

                        metadata.append(f"  {file_path}\n")
                    if master:
                        master_data.append("file:\n")
                        for file_path in data[system][game]['file'].splitlines():
                            master_data.append(f"  ./{system}{file_path[1:]}\n")

                if data[system][game]['developer'] is not None:
                    line = f"developer: {data[system][game]['developer']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['publisher'] is not None:
                    line = f"publisher: {data[system][game]['publisher']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['genre'] is not None:
                    line = f"genre: {data[system][game]['genre']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['description'] is not None:
                    line = f"description: {data[system][game]['description']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['release'] is not None:
                    line = f"release: {data[system][game]['release']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['players'] is not None:
                    line = f"players: {data[system][game]['players']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                if data[system][game]['rating'] is not None:
                    line = f"rating: {data[system][game]['rating']}\n"

                    metadata.append(line)
                    if master:
                        master_data.append(line)

                # Retrieve assets
                if game in media[system]:

                    for item in media[system][game]:
                        asset_code = item.parent.name
                        asset_path = f"./media/{asset_code}/{item.name}"
                        asset = f"assets.{asset_code}: {asset_path}\n"

                        metadata.append(asset)

                        if master:
                            master_path = f"./{system}/media/{asset_code}/{item.name}"
                            master_asset = f"assets.{asset_code}: {master_path}\n"
                            master_data.append(master_asset)

                metadata.append("\n")
                if master:
                    master_data.append("\n")

        print("[ Done ]")

        with open(BASE_PATH/system/'metadata.txt', 'w+', encoding='utf-8') as file:
            for line in metadata:
                file.write(line)

    if master:
        print(
            "  . . > Creating ./metadata.txt... (e.g. master metadata.txt)",
            end="     ")
        print("[ Done ]")
        master_file = open(
            BASE_PATH/'metadata.txt',
            'w+',
            encoding='utf-8')
        for line in master_data:
            master_file.write(line)
        master_file.close()


def backup_media(games, media, collections_to_clean):

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

                for item in value:
                    parent_name = item.parent.name
                    item_name = item.name
                    asset_dir = backup_dir / parent_name

                    if asset_dir.is_dir() is False:
                        Path.mkdir(asset_dir)

                    source_backup = f"{parent_name}/{item_name}"
                    to_backup = asset_dir/item_name

                    try:
                        item.rename(to_backup)
                        backed_up += 1
                    except Exception:
                        print(f"  . . > {source_backup}...", end="     ")
                        print("[ Error ]")

    if backed_up > 0:
        return f"[ {backed_up} assets backed up ]"
    else:
        return "[ Nothing to back up ]"


def main():
    # Configuration file
    try:
        print("  > Checking configuration file...", end="     ")
        configuration = init_config(CONFIG_PATH)
        print("[ Done ]")
    except FileNotFoundError:
        raise ValueError("[ File Not Found ]")
    except Exception as err:
        raise ValueError(err)

    print(flush=True)

    # Generate data

    try:
        print("  > Generating data...", end="     ")
        data = generate_data(configuration['systems']['available'])
    except ValueError as err:
        raise ValueError(err)
    except Exception:
        raise ValueError("[ Unknown Error ]")

    print(flush=True)

    # Getting games in each folder
    try:
        print("  > Getting games in each folder...", end="     ")
        games = get_games(configuration['systems']['available'])
        print("[ Done ]")
    except Exception:
        raise ValueError("[ Unknown Error ]")

    print(flush=True)

    # Getting media in each folder
    try:
        print("  > Getting media in each folder...", end="     ")
        media = get_media(configuration['systems']['available'])
        print("[ Done ]")
    except Exception:
        raise ValueError("[ Unknown Error ]")

    print(flush=True)

    # Create metadata files
    try:
        print("  > Creating metadata files...")
        create_metadata(
            data,
            games,
            media,
            configuration['systems']['available'],
            configuration["bellerophon"]["master_data"])
    except Exception as err:
        raise ValueError(err)

    print(flush=True)

    if configuration["bellerophon"]["clean_media"]:
        # Backup unused media files
        try:
            print("  > Checking unused media files...", end="     ")
            backup = backup_media(
                games,
                media,
                configuration["bellerophon"]["collections_to_clean"])
            print(backup)

        except Exception as err:
            raise ValueError(err)


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
