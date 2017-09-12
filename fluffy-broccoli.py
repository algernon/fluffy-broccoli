#! /usr/bin/env python3
## fluffy-broccoli -- MPD #NowPlaying -> Mastodon bot
## Copyright (C) 2017  Gergely Nagy
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
import argparse
import os
import os.path

CONFIG_DIR = os.path.expanduser("~/.config/fluffy-broccoli")
CLIENT_CREDS = os.path.join(CONFIG_DIR, "client.creds")
USER_CREDS = os.path.join(CONFIG_DIR, "user.creds")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def mainLoop(mastodonClient, mpdClient):
    print("# Entering main loop...")
    previousFile = None

    while True:
        mpdClient.idle("player")
        if mpdClient.status()["state"] != "play":
            continue
        song = mpdClient.currentsong()
        if song["file"] == previousFile:
            continue
        previousFile = song["file"]
        nowPlaying = "{artist} - {title} ({album})".format(**song)
        print(nowPlaying)
        mastodonClient.toot (nowPlaying + "\n\n#NowPlaying")

def loadConfig():
    print("# Loading configuration...")
    with open(CONFIG_FILE, "r") as f:
        config = f.read()
    return config

def configure():
    print ("# Configuring fluffy-broccoli")
    instanceURL = input("Enter the URL of your instance: ")
    userName = input("Enter your email (used only for initial setup): ")
    password = input("Enter your password (used only for initial setup): ")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    Mastodon.create_app(
        "fluffy-broccoli",
        api_base_url=instanceURL,
        to_file=CLIENT_CREDS,
    )
    os.chmod(CLIENT_CREDS, 0o600)

    botAPI = Mastodon(
        api_base_url=instanceURL,
        client_id = CLIENT_CREDS,
    )
    botAPI.log_in(
        userName,
        password,
        to_file = USER_CREDS,
    )
    os.chmod(USER_CREDS, 0o600)

    with open(CONFIG_FILE, "w") as f:
        f.write(instanceURL)

def main():
    if not os.path.exists(CONFIG_FILE) or not os.path.exists(CLIENT_CREDS) or not os.path.exists(USER_CREDS):
        configure()
    config = loadConfig()

    mastodonClient = Mastodon(
        api_base_url=config,
        client_id=CLIENT_CREDS,
        access_token=USER_CREDS
    )
    mpdClient = MPDClient()
    mpdClient.connect("localhost", 6600)

    mainLoop(mastodonClient, mpdClient)

if __name__ == "__main__":
    main()
