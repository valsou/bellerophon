#!/usr/bin/env python
"""Bellerophon is a companion for Pegasus-frontend application.

Bellerophon generate metadata.txt files accordingly to games
and gamelist.xml files. It also backup any asset that is not used.
"""

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import toml


start = datetime.now()

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
    'mp4'
]


def init_config(configuration_path):
    systems = {}
    config_file = toml.load(configuration_path)
    global_path = config_file['global']['path']
    systems_unavailable = []
    systems_available = {}

    for folder in config_file['systems'].keys():

        if folder in BASE_FOLDERS:
            # Retrieve items
            shortname = config_file['systems'][folder]['shortname']
            collection = config_file['systems'][folder]['collection']
            dict_extension = config_file['systems'][folder]['extension']

            extension = [
                x.strip() for x
                in dict_extension.split(',')]

            if "launch" in config_file['systems'][folder]:
                launch = config_file['systems'][folder]['launch']
            else:
                core = config_file['systems'][folder]['core']
                concat_launch = config_file['global']['launch'].replace(
                    "<PATH_VARIABLE>",
                    global_path)
                launch = (
                    f'''{concat_launch}
  -e LIBRETRO /data/data/com.retroarch/cores/{core}
  -e SDCARD {global_path}/{folder}''')

            item = {
                folder: {
                    "collection": collection,
                    "shortname": shortname,
                    "extension": extension,
                    "launch": launch
                }
            }

            # Availables games
            systems_available.update(item)

        systems_unavailable.append(folder)

    systems.update({
        "systems": {
            "available": systems_available,
            "unavailable": systems_unavailable
        }
    })

    return systems


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
        gamename = Path(gamepath).name[:-len(Path(gamepath).suffix)]
        gamepath_wext = Path(gamepath).name[:-len(Path(gamepath).suffix)]

        if gameid != 0 and gameid == last_game[0] and bool(games_dict):
            path = games_dict[last_game[1]]["file"]
            gamepath = path + f"\n  {gamepath}"
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

        last_game = [gameid, gamepath_wext]

    return games_dict


def generate_data(systems):
    data = {}
    iter = 0

    for system in systems.keys():

        if iter == 0:
            print("")

        gamelist_path = BASE_PATH / system / 'gamelist.xml'

        if gamelist_path.is_file():

            parent_folder = gamelist_path.parent.name
            print(
                f"  . . > Parsing {parent_folder}/gamelist.xml...",
                end="     ")

            data.update({
                gamelist_path.parent.name: parse_gamelist(gamelist_path)})
            print("[ Done ]")

        else:
            parent_folder = gamelist_path.parent.name
            print(
                f"  . . > Parsing {parent_folder}/gamelist.xml...",
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
                str(x.name)[:-len(x.suffix)] for x
                in current_path.iterdir()
                if x.is_file() and str(x.suffix)[1:] in games_suffix]
            games_in_folders.update({
                str(folder): games
            })

    return games_in_folders


def sort_media(media):
    sorted_media = {}

    for key, value in sorted(media.items()):
        sorted_media.setdefault(value, []).append(key)

    return sorted_media


def get_media(systems):
    media_in_folders = {}
    systems_in_config = systems.keys()

    for system in systems_in_config:
        media_path = Path(BASE_PATH/system/'media')
        media = {
            x: str(x.name)[:-len(x.suffix)] for x
            in media_path.rglob('*')
            if x.suffix[1:] in MEDIA_EXT}
        sorted_media = sort_media(media)
        media_in_folders.update({
            system: sorted_media
        })

    return media_in_folders


def create_metadata(data, games, media, parameters):

    def append_or_not(label, line):
        if line is not None:
            return f'{label}: {line}\n'
        return ""

    for system in data.keys():
        print(
            f"  . . > Creating {system}/metadata.txt...",
            end="     ")

        file = open(
            BASE_PATH/system/'metadata.txt',
            'w+',
            encoding='utf-8')

        # Generate system header
        for key, value in parameters[system].items():

            if isinstance(value, list):
                value = ','.join(value)

            file.write(f"{key}: {value}\n")

        file.write("\n")

        for game in games[system]:

            if game in data[system].keys():

                file.write(
                    append_or_not(
                        "game",
                        data[system][game]['game']))

                file.write(
                    append_or_not(
                        "file",
                        data[system][game]['file']))

                file.write(
                    append_or_not(
                        "developer",
                        data[system][game]['developer']))

                file.write(
                    append_or_not(
                        "publisher",
                        data[system][game]['publisher']))

                file.write(
                    append_or_not(
                        "genre",
                        data[system][game]['genre']))

                file.write(
                    append_or_not(
                        "description",
                        data[system][game]['description']))

                file.write(
                    append_or_not(
                        "release",
                        data[system][game]['release']))

                file.write(
                    append_or_not(
                        "players",
                        data[system][game]['players']))

                file.write(
                    append_or_not(
                        "rating",
                        data[system][game]['rating']))

                # Retrieve assets
                if game in media[system]:

                    for item in media[system][game]:
                        asset_code = item.parent.name
                        asset_path = f"./media/{asset_code}/{item.name}"
                        asset = f"assets.{asset_code}: {asset_path}\n"
                        file.write(asset)

                file.write("\n")

        print("[ Done ]")

        file.close()


def backup_media(games, media):

    backed_up = False

    for system in games.keys():

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
                        print(f"  . . > {source_backup}...", end="     ")
                        item.rename(to_backup)
                        print("[ Backed up ]")
                        backed_up = True
                    except Exception:
                        print("[ Error ]")

    return backed_up


def main():
    # Configuration file
    try:
        print("  > Checking configuration file...", end="     ")
        configuration = init_config(CONFIG_PATH)
        print("[ Done ]")
    except FileNotFoundError:
        raise ValueError("[ File Not Found ]")
    except Exception:
        raise ValueError("[ Unknown Error ]")

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
            configuration['systems']['available'])
    except Exception as err:
        raise ValueError(err)

    print(flush=True)

    # Backup unused media files
    try:
        print("  > Checking unused media files...", end="     ")
        backup = backup_media(games, media)

        if backup is False:
            print("[ All good ]")

    except Exception as err:
        raise ValueError(err)


if __name__ == "__main__":
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
