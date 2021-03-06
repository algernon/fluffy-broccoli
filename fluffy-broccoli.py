#! /usr/bin/env python3
## fluffy-broccoli -- MPD #NowPlaying -> Mastodon bot
## Copyright (C) 2017, 2018  Gergely Nagy
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

from mpd import MPDClient
from mastodon import Mastodon
from urllib.parse import quote
from xdg import xdg_config_home

import configparser
import io
import os
import os.path
import string
import sh

CONFIG_DIR = xdg_config_home().joinpath("fluffy-broccoli")
CONFIG_FILE = CONFIG_DIR.joinpath("config.ini")

DEFAULTS = {
    "mpd": {
        "host": "localhost",
        "port": 6600,
    },
    "fluffy-broccoli": {
        "format": "{artist} - {title} ({album})",
        "tags": "NowPlaying",
        "musicbrainz_lookup": "no",
    }
}


def findBeetRoot():
    try:
        buf = io.StringIO()
        sh.cut(sh.grep(sh.beet.config(), "^directory:"),
               "-d", ":", "-f2", _out=buf)
    except sh.CommandNotFound:
        return ""
    return os.path.expanduser(buf.getvalue().strip())


def findMusicBrainzAlbum(config, file):
    beet_dir = config["fluffy-broccoli"]["beet_directory"]
    if beet_dir is None:
        return None
    try:
        buf = io.StringIO()
        sh.beet.list("-f", "$mb_albumid",
                     "path:" + os.path.join(beet_dir, file), _out=buf)
    except sh.CommandNotFound:
        return None
    id = buf.getvalue().strip()
    if id == "":
        return None
    else:
        return id


class EmptyFallbackFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        try:
            return string.Formatter.get_value(self, key, args, kwargs)
        except KeyError:
            return ""


def mainLoop(config, mastodonClient, mpdClient):
    print("# Entering main loop...")
    fmt = EmptyFallbackFormatter()
    previousFile = None
    tags = " ".join(["#" + tag
                     for tag in
                     config["fluffy-broccoli"]["tags"].split(" ")])

    while True:
        mpdClient.idle("player")
        if mpdClient.status()["state"] != "play":
            continue
        song = mpdClient.currentsong()
        if song["file"] == previousFile:
            continue
        previousFile = song["file"]
        scrobbled_parts = [quote(song["artist"]), quote(song["title"])]
        song["scrobble_uri"] = "/artist/{0}/track/{1}".format(*scrobbled_parts)
        nowPlaying = fmt.format(config["fluffy-broccoli"]["format"], **song)
        if config["fluffy-broccoli"].getboolean("musicbrainz_lookup"):
            albumId = findMusicBrainzAlbum(config, song["file"])
            if albumId is not None and len(albumId) > 10:
                nowPlaying += " | https://musicbrainz.org/release/" + albumId
        if tags:
            nowPlaying += "\n\n" + tags
        print("# PLAYING:")
        for line in nowPlaying.splitlines():
            print("# ", line)
        mastodonClient.status_post(nowPlaying, visibility="unlisted")


def loadConfig():
    print("# Loading configuration...")
    config = configparser.ConfigParser()
    config["mpd"] = DEFAULTS["mpd"]
    config["fluffy-broccoli"] = DEFAULTS["fluffy-broccoli"]
    config["fluffy-broccoli"]["beet_directory"] = findBeetRoot()

    config.read(CONFIG_FILE)

    beet_dir = config["fluffy-broccoli"]["beet_directory"]
    config["fluffy-broccoli"]["beet_directory"] = os.path.expanduser(beet_dir)
    return config


def configure():
    def opener(path, flags):
        return os.open(path, flags, mode=0o600)

    print("# Configuring fluffy-broccoli")
    instanceURL = input("Enter the URL of your instance: ")
    userName = input("Enter your email (used only for initial setup): ")
    password = input("Enter your password (used only for initial setup): ")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    cID, cSecret = Mastodon.create_app(
        "fluffy-broccoli",
        api_base_url=instanceURL,
    )

    botAPI = Mastodon(
        api_base_url=instanceURL,
        client_id=cID,
        client_secret=cSecret
    )
    accessToken = botAPI.log_in(
        userName,
        password,
    )

    config = configparser.ConfigParser()
    config["mpd"] = DEFAULTS["mpd"]
    config["fluffy-broccoli"] = DEFAULTS["fluffy-broccoli"]
    config["mastodon"] = {
        "instance_url": instanceURL,
        "client_id": cID,
        "client_secret": cSecret,
        "access_token": accessToken,
    }

    with open(CONFIG_FILE, "w", opener=opener) as f:
        config.write(f)


def main():
    if not os.path.exists(CONFIG_FILE):
        configure()
    config = loadConfig()

    mastodonClient = Mastodon(
        api_base_url=config["mastodon"]["instance_url"],
        client_id=config["mastodon"]["client_id"],
        client_secret=config["mastodon"]["client_secret"],
        access_token=config["mastodon"]["access_token"]
    )
    mpdClient = MPDClient()
    mpdClient.connect(config["mpd"]["host"], config["mpd"]["port"])
    if "password" in config["mpd"] and config["mpd"]["password"] is not None:
        mpdClient.password(config["mpd"]["password"])

    mainLoop(config, mastodonClient, mpdClient)


if __name__ == "__main__":
    main()
