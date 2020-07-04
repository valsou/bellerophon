from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import toml
from glob import glob
from sys import stdout
import os

start = datetime.now()

#--- BELLEROPHON ---#
#--- version 0.1 ---#

#--- constants ---#
BASE_PATH = Path.cwd()
MEDIA_EXT = [
    'jpg',
    'jpeg',
    'png',
    'mp4'
]

def initConfig(config_file):
    systems_in_config = config_file['systems'].keys()
    global_launch = str(config_file['global']['launch'])
    global_path = str(config_file['global']['path'])
    
    systems_unavailable = []
    systems_available = {}
    systems = {}

    #::: Folders in BASE_PATH
    all_folders = [x.name for x in BASE_PATH.iterdir() if x.is_dir()]
    
    for folder in systems_in_config:
        if folder in all_folders:
            #... Retrieve items
            shortname = str(config_file['systems'][folder]['shortname'])
            collection = str(config_file['systems'][folder]['collection'])
            extension = [x.strip() for x in str(config_file['systems'][folder]['extension']).split(',')]
            if "launch" in config_file['systems'][folder]:
                launch = str(config_file['systems'][folder]['launch'])         
            else:
                core = str(config_file['systems'][folder]['core'])
                launch = (  f"{global_launch}\n"
                            f"  -e LIBRETRO /data/data/com.retroarch/cores/{core}\n"
                            f"  -e SDCARD {global_path}{folder}" )

            item = {
                folder: {
                    "collection": collection,
                    "shortname": shortname,
                    "extension": extension,
                    "launch": launch
                }
            }
            #.....

            #... Availables games
            systems_available.update( item )
            #.....

        else:
            #... Unavailables games
            systems_unavailable.append(folder)
            #.....


    systems.update( {
        "global": {
            "launch": global_launch,
            "path": global_path
        },
        "systems": {
            "available": systems_available,
            "unavailable": systems_unavailable
        } 
    } )

    return systems

def parseGamelist(file):
    tree = ET.parse(file)
    root = tree.getroot()
    games_dict = {}
    last_game = [ 0, ""]
    path_increment = ""

    def instanceNode(node, extra=None):
        if node is not None and node.text != None:
            if not extra:
                return node.text
            elif extra == "release":
                return datetime.strptime(node.text, '%Y%m%dT%H%M%S').strftime('%Y-%m-%d')
            elif extra == "players":
                number = str(node.text).split('-')
                players = '1'
                if (len(number) > 1):
                    players = number[1]
                return players
            elif extra == "rating":
                percentage = float(node.text) * 100
                rating = str(int(percentage)) + '%'
                return rating
        else:
            return None

    for game in root.findall('game'):

        gamename = instanceNode(game.find('name'))
        gamepath = instanceNode(game.find('path'))
        gamepath_wext = Path(gamepath).name[:-len(Path(gamepath).suffix)]
        developer = instanceNode(game.find('developer'))     
        publisher = instanceNode(game.find('publisher'))
        genre = instanceNode(game.find('genre'))
        description = instanceNode(game.find('desc'))
        release = instanceNode(game.find('releasedate'), "release")
        players = instanceNode(game.find('players'), "players")
        rating = instanceNode(game.find('rating'), "rating")

        if 'id' in game.attrib:
            gameid = int(game.attrib['id'])
        else:
            gameid = 0

        if gameid != 0 and gameid == last_game[0] and bool(games_dict):
            path = games_dict[last_game[1]]["file"]
            gamepath = path + f"\n  {gamepath}"
            del games_dict[last_game[1]]

        games_dict.update( {
            Path(gamepath).name[:-len(Path(gamepath).suffix)]: {
                "game": gamename,
                "file": gamepath,
                "developer": developer,
                "publisher": publisher,
                "genre": genre,
                "description": description,
                "release": release,
                "players": players,
                "rating": rating
            }
        } )

        last_game = [ gameid,gamepath_wext ]
    
    return games_dict

def generateData(systems, games_in_folders):
    data = {}
    for system in systems.keys():
        gamelist_path = BASE_PATH / system / 'gamelist.xml'
        # metadata_path = BASE_PATH / system / 'metadata.txt'
        if gamelist_path.is_file():
            stdout.write(f"  . . > Parsing {gamelist_path.parent.name}/gamelist.xml...")
            try:
                data.update( {
                    gamelist_path.parent.name: parseGamelist(gamelist_path)
                } )
                stdout.write("     [ Done ]")
            except Exception:
                stdout.write("     [ Error ]")
            finally:
                stdout.write("\n")
                stdout.flush()
        else:
            stdout.write(f"  . . > Parsing {gamelist_path.parent.name}/gamelist.xml...     [ Not found ]\n")
            stdout.flush()

    return data

def getGames(systems):
    games_in_folders = {}
    all_folders = [x.name for x in BASE_PATH.iterdir() if x.is_dir()]
    systems_in_config = systems.keys()

    for folder in systems_in_config:
        if folder in all_folders:
            current_path = BASE_PATH / folder
            games_suffix = [x for x in systems[folder]['extension']]  
            games = [str(x.name)[:-len(x.suffix)] for x in current_path.iterdir() if x.is_file() and str(x.suffix)[1:] in games_suffix]  
            games_in_folders.update( {
                str(folder): games
            } )

    return games_in_folders

def sortMedia(media):
    sorted_media = {}
    for key, value in sorted(media.items()):
        sorted_media.setdefault(value, []).append(key)
    return sorted_media

def getMedia(systems):
    media_in_folders = {}
    systems_in_config = systems.keys()

    for system in systems_in_config:
        media_path = Path(BASE_PATH / system / 'media')
        media = {x:str(x.name)[:-len(x.suffix)] for x in media_path.rglob('*') if x.suffix[1:] in MEDIA_EXT}
        sorted_media = sortMedia(media)
        media_in_folders.update( {
            system: sorted_media
        } )
    
    return media_in_folders

def createMetadata(data, games, media, parameters):
    for system in data.keys():
        output = ""
        try:
            stdout.write(f"  . . > Creating {system}/metadata.txt...")
            games_dict = []

            for k, v in parameters[system].items():
                if type(v) == list:
                    v = ','.join(v)
                games_dict.append(f"{k}: {v}\n")
            
            games_dict.append("\n")

            for game in games[system]:

                if game in data[system].keys():

                    if data[system][game]['game'] != None:
                        games_dict.append(f"game: {data[system][game]['game']}\n")        

                    if data[system][game]['file'] != None:
                        games_dict.append(f"file: {data[system][game]['file']}\n")
                    
                    if data[system][game]['developer'] != None:
                        games_dict.append(f"developer: {data[system][game]['developer']}\n")
                            
                    if data[system][game]['publisher'] != None:
                        games_dict.append(f"publisher: {data[system][game]['publisher']}\n")

                    if data[system][game]['genre'] != None:
                        games_dict.append(f"genre: {data[system][game]['genre']}\n")

                    if data[system][game]['description'] != None:
                        games_dict.append(f"description: {data[system][game]['description']}\n")
                    
                    if data[system][game]['release'] != None:
                        games_dict.append(f"release: {data[system][game]['release']}\n")

                    if data[system][game]['players'] != None:
                        games_dict.append(f"players: {data[system][game]['players']}\n")

                    if data[system][game]['rating'] != None:
                        games_dict.append(f"rating: {data[system][game]['rating']}\n")

                    # if 'id' in game.attrib:
                    #     games_dict.append(f"x-id: {game.attrib['id']}\n")

                    # if 'source' in game.attrib:
                    #     games_dict.append(f"x-source: {game.attrib['source']}\n")

                    #... Retrieve assets
                    if game in media[system]:
                        for item in media[system][game]:
                            asset_code = item.parent.name
                            asset_path = f"./media/{asset_code}/{item.name}"
                            games_dict.append(f"assets.{asset_code}: {asset_path}\n")
                    #...............

                    games_dict.append("\n")

            for line in games_dict:
                output += line

            f = open(BASE_PATH / system / 'metadata.txt', 'w+', encoding='utf-8')
            f.write(output)
            f.close()

            stdout.write("     [ Done ]")

        except Exception:
            stdout.write("     [ Error ]")
        finally:
            stdout.write("\n")
            stdout.flush()

def backupMedia(games, media):
    backed_up = False
    for system in games.keys():
        try:
            for k,v in media[system].items():
                if k not in games[system]:

                    backup_dir = BASE_PATH / system / 'media.backup'

                    if backup_dir.is_dir() is False:
                        Path.mkdir(backup_dir)

                    for item in v:
                        asset_dir = BASE_PATH / system / 'media.backup' / item.parent.name

                        if asset_dir.is_dir() is False:
                            Path.mkdir(asset_dir)
                        
                        to_backup = BASE_PATH / system / 'media.backup' / item.parent.name / item.name
                        item.rename(to_backup)

                        stdout.write(f"\n  . . > {system}/{item.parent.name}/{item.name}...     [ Backed up ]\n")
                        backed_up = True

        except Exception:
            stdout.write("     [ Error ]")
        finally:
            stdout.flush()

    return backed_up

def missingAssets():
    pass

def main():
    #::: Configuration file
    stdout.write("  > Checking configuration file...")
    try:
        config_path = BASE_PATH / 'bellerophon.conf'
        configuration = initConfig(toml.load(config_path))
        stdout.write("     [ Done ]")
    except Exception:
        stdout.write("     [ File does not exist ]")
        raise Exception
    finally:
        stdout.write("\n\n")
        stdout.flush()
    #:::::

    #::: Getting games in each folder
    stdout.write("  > Getting games in each folder...")
    try:
        games = getGames(configuration['systems']['available'])
        stdout.write("     [ Done ]")
    except Exception:
        stdout.write("     [ Error ]")
        raise Exception
    finally:
        stdout.write("\n\n")
        stdout.flush()
    #:::::

    #::: Generate data
    stdout.write("  > Generating data...\n")
    data = generateData(configuration['systems']['available'], games)
    if not data:
        return
    stdout.write("\n")
    stdout.flush()
    #:::::

    #::: Getting media in each folder
    stdout.write("  > Getting media in each folder...")
    try:
        media = getMedia(configuration['systems']['available'])
        stdout.write("     [ Done ]")
    except Exception:
        stdout.write("     [ Error ]")
        raise Exception
    finally:
        stdout.write("\n\n")
        stdout.flush()
    #:::::

    #::: Create metadata files
    stdout.write("  > Creating metadata files...\n")
    createMetadata(data, games, media, configuration['systems']['available'])
    stdout.write("\n")
    stdout.flush()
    #:::::

    #::: Backup unused media files
    stdout.write("  > Checking unused media files...")
    backup = backupMedia(games, media)
    if backup == False:
        stdout.write("     [ All good ]")
    stdout.write("\n")
    stdout.flush()
    #:::::

if __name__ == "__main__":
    begin_message = '''
  ≠------------------------------------------------≠
  ¦    * . BELLEROPHON * . *                       ¦
  ¦                                                ¦
  ¦              - a Pegasus-frontend companion    ¦
  ≠------------------------------------------------≠
  '''
    print(begin_message)
    try:
        main()
    except Exception:
        pass
    finish = datetime.now()
    end_message = f'''
  [ Bellorephon took {round((finish-start).total_seconds(),2)} s ]

  Hope the script was helpful. •ᴗ•
    '''
    print(end_message)
    input("")  