# top-songs-dashboard
Implementing a daily updated dashboard tracking the top songs on streaming and radio charts


# Outline of Project

## Data Scraping

### Billboards.com

Using the "Billboard" python library, we can easily collect the top 200 songs for a given day (today or in the past). The purpose of the "build_dataset.py" script is to use the "BillboardScraper" class to collect the top 200 songs for a list of dates, and then add them to the "billboard" SQL table. The concept is this:

1) For every day since some past date, query the API about what the top 200 songs were on that date
2) In order to prevent duplicate data in the SQL table "billboard": Query the table to see if there are any rows from that date
3) Upload the data table straight from the API to SQL

As of now, this portion of the project is not complete. Code still needs to be written for steps 2 and 3

### Future Work

The most interesting addition we can make to this dataset is the following SQL table:
 - each row is a song
 - there is only one row per song
 - the row contains information such as: release date, genre, bpm, key, danceability, and other interesting information about the song

If we can find an API that returns this kind of data when given a song title and artist, then we can create a second SQL table "songs" that when joined with the original "billboard" table, will have a ton of useful information to analyze.

1) Find an API that has interesting data on songs
2) Write an API query class
3) Write a method to prevent duplicate data from being uploaded
4) Write a method to upload data to the "songs" SQL table
