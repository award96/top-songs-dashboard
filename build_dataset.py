import sys
from datetime import date, datetime, timedelta
from BillboardScraper import BillboardScraper
from utilities import create_date_list
from QueryRDS import QueryRDS

"""
USAGE (update database)

 >   python build_dataset.py

RESULT
    Queries the DB to find most recent date
    Collects data from most recent date to today's date
    Uploads to DB

USAGE (build database from scratch, or add specific dates to database)

 >   python build_dataset.py YYYY-MM-DD yyyy-mm-dd

RESULT
    Collects data from YYYY-MM-DD to yyyy-mm-dd
    Uploads to DB

In both cases the DB is queried before inserting new rows in order
to prevent duplicate data.
    If the data to be inserted has the same date as existing data
    the data will not be inserted
    
"""


def update():
    rds = QueryRDS()
    q = "SELECT chart_date FROM charts ORDER BY chart_date DESC LIMIT 1"
    resp = rds.query(q)
    try:
        dt_obj = resp[0][0]
        dt_obj += timedelta(days=1)
    except:
        raise ValueError("""
            Database Query did not return any rows.
            Please use syntax:
                python build_dataset.py [start_date] [end_date]
            In order to populate Database.

            [start_date] format is YYYY-MM-DD
        """
        )
    start_date = dt_obj.strftime("%Y-%m-%d")
    todays_date = datetime.now().strftime("%Y-%m-%d")

    build(start_date, todays_date)

def build(start_date, end_date, max_attempts = 5):
    date_list = create_date_list(start_date, end_date)
    missed_date_list = scrape_dates(date_list)

    attempts = 0
    while len(missed_date_list) > 0 and attempts < max_attempts:
        attempts += 1
        missed_date_list = scrape_dates(missed_date_list)

def scrape_dates(date_list):
    scraper = BillboardScraper("hot-100", date_list)
    scraper.scrape()
    missed_date_list = scraper.missed_dates
    return missed_date_list

if __name__ == "__main__":
    """
    ARGS:
        argv = [python build_dataset, start_date, end_date]

        date format should by YYYY-MM-DD
        no apostrophes or quotes
    """
    if len(sys.argv) <= 1:
        update()
    else:
        start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
        build(start_date, end_date)
        