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
        self.missed_tracks_indices = []
        self._vals = []
        
    def scrape(self):
        # Query charts table to find songs to gather data on
        tracks = self.find_tracks_RDS()
        # Query songs table to prevent duplicate uploads
        tracks = self.remove_duplicates(tracks)

        if len(tracks) == 0:
            print("\nNo new songs to add")
            return
        
        
        MAX_REQ = 50
        sub_tracks_index = [MAX_REQ * i for i in range(len(tracks) // MAX_REQ + 1)]
        sub_tracks_index.append(len(tracks))

        for i in range(len(sub_tracks_index) - 1):
            print(f"\nIteration {i} of Spotify data gathering and SQL uploading")
            print(f"Tracks {sub_tracks_index[i]} : {sub_tracks_index[i + 1]} will be uploaded ({len(tracks) - sub_tracks_index[i]} tracks remaining)")
            sub_tracks = tracks[ sub_tracks_index[i] : sub_tracks_index[i + 1] ]
            # Spotify API data gathered using spotipy library
            ids, titles, artists, raw_data = self.get_song_data(sub_tracks)
            # Reorganize data for SQL upload (list of tuples, each tuple represents a row)
            these_vals = self.parse_data(ids, titles, artists, raw_data)
            self._vals = self._vals + these_vals

            qstring = "INSERT INTO songs (id, title, artist, danceability, energy, song_key, loudness, song_mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration, time_signature) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            num_rows_inserted = self._rds.bigInsert(qstring, these_vals)
            print(f"\n{num_rows_inserted} rows inserted...")

        did_upload = True
                

        

    
        print("\n\nFinished")


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
        # query charts table to find songs to gather data on
        query = f"SELECT DISTINCT(title), artist FROM charts"
        res = self._rds.query(query)
        return res


    def remove_duplicates(self, tracks):
        """
            ARGS
                tracks: tuple of tuples. Each sub tuple is the title and artist of a track
            RETURNS
                list of tuples. Each sub tuple is the title and artist of a track
        """
        title_list, artist_list = list(zip(*tracks))
        # We convert tracks to a list so we can use the remove function

        tracks = list(tracks)
        q = f"SELECT title, artist FROM songs WHERE title IN {title_list} AND artist IN {artist_list}"
        res = self._rds.query(q)

        num_removed = 0
        for row in res:
            try:
                tracks.remove(row)
                num_removed += 1
            except ValueError as e:
                print(f"\nValueError: Cannot remove row as it is not present\n{e}")
                print(f"Attempted to remove:\n{row}")
        print(f"\nAfter removal of {num_removed} duplicates, {len(tracks)} tracks left")
        return tracks
    
    def get_song_data(self, tracks, i=0):

        # We start new ists because the api will not recognize some of the tracks
        # This way we can keep each index of each list corresponding to the same track
        track_ids, track_titles, track_artists = [], [], []
        missed_tracks = []
        missed_tracks_indices = []
        # First get the spotify ID
        for t in tracks:
            title, artist = t[0], t[1]
            t_id = self.get_track_id(title, artist)

            if t_id is None:
                # skip this track
                missed_tracks.append(t)
                missed_tracks_indices.append(i)
                i+=1
                continue
            track_ids.append(t_id)
            track_titles.append(title)
            track_artists.append(artist)
            i+=1

        # Usually due to a difference in representation of ', *, \, and other problematic characters
        self.missed_tracks += missed_tracks
        self.missed_tracks_indices += missed_tracks_indices
        print(f"\n\n{len(missed_tracks)} out of {len(tracks)} tracks could not be found on the Spotify API")

        # Then use the spotify ID to get more information
        results = self._api.audio_features(tracks=track_ids)

        if len(results) != len(track_ids):
            print(f"results length: {len(results)} , not equal to track id's length: {len(track_ids)}")
            print("Skipping these tracks")
            return [], [], [], []
    
        return track_ids, track_titles, track_artists, results
            

    def get_track_id(self, title, artist, recursive_stop = 0, isRetry = False):

        """
            ARGS
                title (str):    title of the track
                artist (str):   artist of the track
                recursive_stop (int): each time this method calls itself, add 1 to recursive stop.
                                        Prevents infinite loop
                isRetry (bool): If this is a retry we will include the artist in the API request
                                Normally we exclude the artist from our query as the charts data represents multiple artists
                                in a very useless way.
        """

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

        # No matches were found if the code got to here
        # We retry now using the artist in the query 
        return self.get_track_id(title, artist, recursive_stop + 1, isRetry=True)
            

    def get_spotify_creds(self):
        spotify_creds = {}
        with open(CREDS_FILENAME, 'r') as file:
            for line in file:
                l, r = line.split("=")
                r = r.replace("\n", "")
                spotify_creds[l] = r
        self._spotify_creds = spotify_creds
    





