from datetime import date
from BillboardScraper import BillboardScraper
from utilities import create_date_list

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
    build('2019-07-13', "2022-05-10")