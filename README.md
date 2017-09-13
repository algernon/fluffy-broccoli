Fluffy Broccoli
===============

A [Mastodon][mastodon] bot that posts what you are listening to. Uses [mpd][mpd]
to figure out the current track.

 [mastodon]: https://joinmastodon.org/
 [mpd]: https://www.musicpd.org/

See [my bot][algernon:fluffy] for an example of how it looks.

 [algernon:fluffy]: https://trunk.mad-scientist.club/@fluffy_broccoli

Installation
------------

This little bot requires Python 3.2+, Mastodon.py, and python-mpd2, all
conveniently listed in the `requirements.txt` file. As such, installing the
dependencies is as simple as `pip install -r requirements.txt`. Once
dependencies are installed, just run the `fluffy-broccoli.py` script and follow
the prompts.

Configuration will be saved in `~/.config/fluffy-broccoli/config.ini`, you are
free to edit the settings therein. The file will not be written to outside of
the initial configuration. See the `extra/fluffy-broccoli.example.ini` for a
list of available options within that file.

License
-------

Copyright (C) 2017 Gergely Nagy, licensed under the GNU GPLv3+.
