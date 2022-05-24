from decimal import DivisionByZero
from QueryRDS import QueryRDS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import time
import pandas as pd
import numpy as np

CREDS_FILENAME = "spotify.txt"


class SpotifyScraper():
    def __init__(self):
        self._rds = QueryRDS()
        self.get_spotify_creds()

        os.environ["SPOTIPY_CLIENT_ID"] = self._spotify_creds["SPOTIPY_CLIENT_ID"]
        os.environ["SPOTIPY_CLIENT_SECRET"] = self._spotify_creds["SPOTIPY_CLIENT_SECRET"]
        self._api = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

        self.missed_tracks = []
        
    def scrape(self):
        tracks = self.find_tracks_RDS()
        tracks = self.remove_duplicates(tracks)
        if len(tracks) == 0:
            print("\nNo new songs to add")
            return
        ids, titles, artists, raw_data = self.get_song_data(tracks)

        self._vals = self.parse_data(ids, titles, artists, raw_data)

        qstring = "INSERT INTO songs (id, title, artist, danceability, energy, song_key, loudness, song_mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration, time_signature) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        num_rows_inserted = self._rds.bigInsert(qstring, self._vals)

    
        print(f"\n\nFinished.\n{num_rows_inserted} rows inserted.")


    def parse_data(self, ids, titles, artists, raw_data):
        vals = []
        # for SQL insertion, each row needs to be a tuple
        colnames = [
            'danceability',
            'energy',
            'key',
            'loudness',
            'mode',
            'speechiness',
            'acousticness',
            'instrumentalness',
            'liveness',
            'valence',
            'tempo',
            'duration_ms',
            'time_signature'
        ]
        
        for i in range(len(ids)):
            this_row = [ids[i], titles[i], artists[i]]
            for col in colnames:
                this_row.append(raw_data[i][col])
            this_row = tuple(this_row)
            vals.append(this_row)
        
        return vals

    def find_tracks_RDS(self):
        query = f"SELECT DISTINCT(title), artist FROM charts"
        res = self._rds.query(query)
        return res


    def remove_duplicates(self, tracks):
        title_list, artist_list = list(zip(*tracks))
        tracks = list(tracks)
        q = f"SELECT title, artist FROM songs WHERE title IN {title_list} AND artist IN {artist_list}"
        res = self._rds.query(q)

        for row in res:
            try:
                tracks.remove(row)
            except ValueError as e:
                print(f"\nValueError: Cannot remove row as it is not there\n{e}")
        print(f"\nAfter removal of duplicates, {len(tracks)} tracks left")
        return tracks
    
    def get_song_data(self, tracks):
        track_ids, track_titles, track_artists = [], [], []

        # First get the spotify ID
        for t in tracks:
            title, artist = t[0], t[1]
            t_id = self.get_track_id(title, artist)

            if t_id is None:
                # skip this track
                self.missed_tracks.append(t)
                continue
            track_ids.append(t_id)
            track_titles.append(title)
            track_artists.append(artist)

        # Then use the spotify ID to get more information
        try:
            print(f"\n\nRATIO OF MISSING: {len(self.missed_tracks)/len(tracks)}\n")
        except ZeroDivisionError:
            pass
        results = self._api.audio_features(tracks=track_ids)
        if len(results) != len(track_ids):
            raise ValueError(f"results length: {len(results)} , not equal to track id's length: {len(track_ids)}")
        return track_ids, track_titles, track_artists, results
            

    def get_track_id(self, title, artist, recursive_stop = 0, isRetry = False):

        if recursive_stop > 2:
            return None
        
        query = f"track:{title}"
        if isRetry:
            # including artist is risky because billboards includes multiple artists in data
            # Therefore we only include artists if we already couldn't find the data
            query = f"track:{title} artist:{artist}"
        
        try:
            results = self._api.search(q=query, type='track', limit=50)
        except SpotifyException as e: # exception corresponding to bad http requests
            print(e)
            print("Waiting 30 seconds...")
            time.sleep(30)
            return self.get_track_id(title, artist, recursive_stop + 1)

        try:
            items = results["tracks"]["items"]
            for item in items:
                for this_artist_dict in item['artists']:
                    this_artist = this_artist_dict['name']
                    if this_artist in artist:
                        # we are on the right item
                        track_id = item["id"]
                        return track_id
        except KeyError as e:
            print(f"\nERROR...\n{e}")
            print(title)
            print(artist)
            # There is an error so return none
            return None
        # None were matches so return None
        print("\nNo match for")
        print(title)
        print(artist)
        return self.get_track_id(title, artist, recursive_stop + 1, isRetry=True)
            

    def get_spotify_creds(self):
        spotify_creds = {}
        with open(CREDS_FILENAME, 'r') as file:
            for line in file:
                l, r = line.split("=")
                r = r.replace("\n", "")
                spotify_creds[l] = r

        self._spotify_creds = spotify_creds
    



"""
[{'danceability': 0.641,
  'energy': 0.78,
  'key': 3,
  'loudness': -5.138,
  'mode': 1,
  'speechiness': 0.0852,
  'acousticness': 0.0206,
  'instrumentalness': 0,
  'liveness': 0.143,
  'valence': 0.693,
  'tempo': 98.004,
  'type': 'audio_features',
  'id': '4PuAqZlL1tkidkuxfDlLbF',
  'uri': 'spotify:track:4PuAqZlL1tkidkuxfDlLbF',
  'track_href': 'https://api.spotify.com/v1/tracks/4PuAqZlL1tkidkuxfDlLbF',
  'analysis_url': 'https://api.spotify.com/v1/audio-analysis/4PuAqZlL1tkidkuxfDlLbF',
  'duration_ms': 179720,
  'time_signature': 4}]
  
"""

