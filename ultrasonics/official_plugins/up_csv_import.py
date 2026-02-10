#!/usr/bin/env python3

"""
up_csv_import

Input plugin for importing playlists and songs from a CSV file.

Two main use-cases are supported:

1. **Exportify-style CSV (default)**
   - One playlist per CSV file (e.g. `Liked_Songs.csv`).
   - The playlist name is taken from the *file name*.
   - Typical Exportify columns:
     - `Track Name`, `Artist Name`, `Album Name`, `Track ID`, `Track URI`, etc.

2. **Generic multi-playlist CSV**
   - A single CSV file contains multiple playlists and a `playlist` column.
   - Expected default CSV format (with header):

        playlist,title,artists,album,date,isrc,location,spotify_id,tidal_id

     - **playlist**: playlist name
     - **title**: track title (required)
     - **artists**: one or more artist names separated by `;` (optional)
     - **album**: album name (optional)
     - **date**: release date as free text (optional)
     - **isrc**: ISRC code (optional)
     - **location**: local file path to the audio file, if any (optional)
     - **spotify_id**: raw Spotify track ID (not URI) (optional)
     - **tidal_id**: raw Tidal track ID (optional)

You can override the column names in the plugin settings if your CSV uses
different headers (for Exportify, sensible defaults are provided).

XDGFX, 2026 (csv import plugin)
"""

import csv
import os

from ultrasonics import logs
from ultrasonics.tools import name_filter

log = logs.create_log(__name__)


handshake = {
    "name": "csv import",
    "description": "import playlists and songs from a csv file",
    "type": ["inputs"],
    "mode": ["playlists"],
    "version": "0.2",
    "settings": [
        {
            "type": "string",
            "value": "This plugin reads playlists and songs from a CSV file and converts them into ultrasonics format.",
        },
        {
            "type": "text",
            "label": "CSV File Path",
            "name": "path",
            "value": "/path/to/playlists.csv",
            "required": True,
        },
        {
            "type": "text",
            "label": "CSV Delimiter",
            "name": "delimiter",
            "value": ",",
        },
        {
            "type": "radio",
            "label": "Has Header Row",
            "name": "has_header",
            "id": "has_header",
            "options": ["Yes", "No"],
        },
        {
            "type": "radio",
            "label": "Playlist Name Source",
            "name": "playlist_source",
            "id": "playlist_source",
            "options": ["From file name", "From CSV column"],
        },
        {
            "type": "string",
            "value": "If you disable the header row, the plugin will assume the columns are in the default order documented in the plugin description.",
        },
        {
            "type": "string",
            "value": "You can optionally override the expected column names below. Leave blank to use the defaults.",
        },
        {
            "type": "text",
            "label": "Playlist Column Name (for multi-playlist CSV)",
            "name": "col_playlist",
            "value": "playlist",
        },
        {
            "type": "text",
            "label": "Title Column Name",
            "name": "col_title",
            "value": "Track Name",
        },
        {
            "type": "text",
            "label": "Artists Column Name",
            "name": "col_artists",
            "value": "Artist Name",
        },
        {
            "type": "text",
            "label": "Album Column Name",
            "name": "col_album",
            "value": "Album Name",
        },
        {
            "type": "text",
            "label": "Date Column Name",
            "name": "col_date",
            "value": "date",
        },
        {
            "type": "text",
            "label": "ISRC Column Name",
            "name": "col_isrc",
            "value": "isrc",
        },
        {
            "type": "text",
            "label": "Location Column Name",
            "name": "col_location",
            "value": "location",
        },
        {
            "type": "text",
            "label": "Spotify ID Column Name",
            "name": "col_spotify_id",
            "value": "Track ID",
        },
        {
            "type": "text",
            "label": "Tidal ID Column Name",
            "name": "col_tidal_id",
            "value": "tidal_id",
        },
        {
            "type": "string",
            "value": "You can use a regex filter on playlist names. Leave it blank to import all playlists.",
        },
        {
            "type": "text",
            "label": "Playlist Name Filter (regex)",
            "name": "filter",
            "value": "",
        },
    ],
}


def _get_field_name(settings_dict, key, default):
    """
    Helper to read a configurable column name from settings, falling back to a default.
    """
    value = (settings_dict.get(key) or "").strip()
    return value or default


def _get_cell(row, header_map, configured_name):
    """
    Helper to get a cell from a DictReader row using a case-insensitive
    column name lookup.
    """
    key = (configured_name or "").strip()
    if not key:
        return ""

    if header_map:
        actual = header_map.get(key.lower(), key)
    else:
        actual = key

    return (row.get(actual) or "").strip()


def _row_to_track(row, field_names, header_map=None):
    """
    Convert a CSV row (dict) into a single track entry in ultrasonics songs_dict format.
    """
    title = _get_cell(row, header_map, field_names["title"])
    if not title:
        # Skip rows without a title
        return None

    track = {
        "title": title,
    }

    # Artists, as a list of names split on ';'
    artists_raw = _get_cell(row, header_map, field_names["artists"])
    if artists_raw:
        artists = [a.strip() for a in artists_raw.split(";") if a.strip()]
        if artists:
            track["artists"] = artists

    album = _get_cell(row, header_map, field_names["album"])
    if album:
        track["album"] = album

    date = _get_cell(row, header_map, field_names["date"])
    if date:
        track["date"] = date

    isrc = _get_cell(row, header_map, field_names["isrc"])
    if isrc:
        track["isrc"] = isrc

    location = _get_cell(row, header_map, field_names["location"])
    if location:
        track["location"] = location

    spotify_id = _get_cell(row, header_map, field_names["spotify_id"])
    tidal_id = _get_cell(row, header_map, field_names["tidal_id"])

    ids = {}
    if spotify_id:
        ids["spotify"] = spotify_id
    if tidal_id:
        ids["tidal"] = tidal_id
    if ids:
        track["id"] = ids

    return track


def run(settings_dict, **kwargs):
    """
    Reads a CSV file and returns a songs_dict in playlists mode.

    For each distinct playlist name in the CSV, a playlist entry is created:

        {
            "name": "<playlist name>",
            "id": {},
            "songs": [<track dicts>]
        }
    """

    component = kwargs["component"]

    if component != "inputs":
        # This plugin only supports input mode.
        raise Exception("up_csv_import only supports 'inputs' component.")

    path = (settings_dict.get("path") or "").strip()
    if not path:
        raise Exception("CSV File Path is required.")

    if not os.path.isfile(path):
        raise Exception(f"CSV file does not exist: {path}")

    delimiter = (settings_dict.get("delimiter") or ",") or ","
    has_header = (settings_dict.get("has_header") or "Yes") == "Yes"
    playlist_source = (settings_dict.get("playlist_source") or "From file name").strip()

    # Resolve column names
    field_names = {
        "playlist": _get_field_name(settings_dict, "col_playlist", "playlist"),
        "title": _get_field_name(settings_dict, "col_title", "Track Name"),
        "artists": _get_field_name(settings_dict, "col_artists", "Artist Name"),
        "album": _get_field_name(settings_dict, "col_album", "Album Name"),
        "date": _get_field_name(settings_dict, "col_date", "date"),
        "isrc": _get_field_name(settings_dict, "col_isrc", "isrc"),
        "location": _get_field_name(settings_dict, "col_location", "location"),
        "spotify_id": _get_field_name(settings_dict, "col_spotify_id", "Track ID"),
        "tidal_id": _get_field_name(settings_dict, "col_tidal_id", "tidal_id"),
    }

    songs_dict = []

    # --- Case 1: playlist name comes from file name (Exportify style) ---
    if playlist_source == "From file name":
        playlist_name = os.path.splitext(os.path.basename(path))[0]
        tracks = []

        with open(path, "r", encoding="utf-8") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                header_map = {h.lower(): h for h in (reader.fieldnames or []) if h}

                for row in reader:
                    track = _row_to_track(row, field_names, header_map=header_map)
                    if not track:
                        continue
                    tracks.append(track)
            else:
                # No header: assume fixed order without playlist column:
                # title, artists, album, date, isrc, location, spotify_id, tidal_id
                reader = csv.reader(f, delimiter=delimiter)
                for row in reader:
                    if not row or all(not (cell or "").strip() for cell in row):
                        continue

                    padded = list(row) + ["" for _ in range(max(0, 8 - len(row)))]

                    row_dict = {
                        field_names["title"]: padded[0],
                        field_names["artists"]: padded[1],
                        field_names["album"]: padded[2],
                        field_names["date"]: padded[3],
                        field_names["isrc"]: padded[4],
                        field_names["location"]: padded[5],
                        field_names["spotify_id"]: padded[6],
                        field_names["tidal_id"]: padded[7],
                    }

                    track = _row_to_track(row_dict, field_names)
                    if not track:
                        continue

                    tracks.append(track)

        if tracks:
            songs_dict.append(
                {
                    "name": playlist_name,
                    "id": {},
                    "songs": tracks,
                }
            )

    # --- Case 2: playlist name comes from CSV column (multi-playlist CSV) ---
    else:
        playlists = {}

        with open(path, "r", encoding="utf-8") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                header_map = {h.lower(): h for h in (reader.fieldnames or []) if h}

                for row in reader:
                    playlist_name = _get_cell(
                        row, header_map, field_names["playlist"]
                    )
                    if not playlist_name:
                        continue

                    track = _row_to_track(row, field_names, header_map=header_map)
                    if not track:
                        continue

                    playlists.setdefault(playlist_name, []).append(track)
            else:
                # No header: use fixed positional mapping in the documented order
                reader = csv.reader(f, delimiter=delimiter)
                for row in reader:
                    if not row or all(not (cell or "").strip() for cell in row):
                        continue

                    # Minimum expected columns: playlist, title
                    if len(row) < 2:
                        continue

                    # Pad row to expected length
                    padded = list(row) + ["" for _ in range(max(0, 9 - len(row)))]

                    playlist_name = (padded[0] or "").strip()
                    if not playlist_name:
                        continue

                    row_dict = {
                        field_names["playlist"]: padded[0],
                        field_names["title"]: padded[1],
                        field_names["artists"]: padded[2],
                        field_names["album"]: padded[3],
                        field_names["date"]: padded[4],
                        field_names["isrc"]: padded[5],
                        field_names["location"]: padded[6],
                        field_names["spotify_id"]: padded[7],
                        field_names["tidal_id"]: padded[8],
                    }

                    track = _row_to_track(row_dict, field_names)
                    if not track:
                        continue

                    playlists.setdefault(playlist_name, []).append(track)

        for name, tracks in playlists.items():
            songs_dict.append(
                {
                    "name": name,
                    "id": {},
                    "songs": tracks,
                }
            )

    # Apply regex filter if provided
    regex = (settings_dict.get("filter") or "").strip()
    if regex:
        songs_dict = name_filter.filter(songs_dict, regex)

    log.info(f"Imported {len(songs_dict)} playlist(s) from CSV file {path}.")
    return songs_dict


def builder(**kwargs):
    """
    Builder simply returns the settings defined in the handshake.
    """
    # For this plugin, the handshake settings are sufficient.
    return handshake["settings"]

