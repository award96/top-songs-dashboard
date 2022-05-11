# top-songs-dashboard
Implementing a daily updated dashboard tracking the top songs on streaming and radio charts

# Requirements
aws.txt
    a txt file in the form of 

    AWS_DB_PW=value
    AWS_DB_HOST=value
    AWS_DB_USER=value
    AWS_DB_DB=value
    AWS_DB_PORT=value


no apostrophes are necessary

an AWS RDS Database
- MySQL
- contains a table called 'charts' with the columns:
  - chart_date DATE
  - title VARCHAR(100)
  - artist VARCHAR(100)
  - image VARCHAR(100)
  - peakPos SMALLINT
  - lastPos SMALLINT
  - weeks SMALLINT
  - chart_rank SMALLINT
  - isNew BOOL

# How to use

In terminal:

    '''
    python build_dataset.py [start_date] [end_date]
    '''
This will gather data from [start_date] to [end_date]

    '''
    python build_dataset.py
    '''
This will query your DB for the most recent date and gather data from that most recent date to today's date

This requires that you have data in your database

[start_date] and [end_date] should be formatted:
    YYYY-MM-DD
with no apostrophes

# Outline of Project

## Data Scraping

### Billboards.com

Using the "Billboard" python library, we can easily collect the top 100 songs for a given day (today or in the past). The purpose of the "build_dataset.py" script is to use the "BillboardScraper" class to collect the top 100 songs for a list of dates, and then add them to the "charts" SQL table. The concept is this:

1) For every day since some past date, query the API about what the top 100 songs were on that date
2) In order to prevent duplicate data in the SQL table "billboard": Query the table to see if there are any rows from that date
3) Upload the data table straight from the API to SQL

This portion of the project is complete

### Future Work

The most interesting addition we can make to this dataset is the following SQL table:
 - each row is a song
 - each song is unique (1 row per song)
 - the row contains information such as: release date, genre, bpm, key, danceability, and any other interesting information about the song.

If we can find an API that returns this kind of data when given a song title and artist, then we can create a second SQL table "songs" that when joined with the original "charts" table, will have a ton of useful information to analyze.

1) Find an API that has interesting data on songs
2) Write an API query class
3) Write a method to find every unique song in the "charts" table
4) Write a method to prevent duplicate data from being uploaded
5) Use the existing "QueryRDS" class to upload data to SQL database

## Data Analysis
TBD

## Automation
We should be able to utilize AWS to automate the process of updating the dataset and analytics dashboard each day with the new top 100


