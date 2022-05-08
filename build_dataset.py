from BillboardScraper import BillboardScraper
from utilities import create_date_list

def build(start_date, end_date):
    date_list = create_date_list(start_date, end_date)
    scraper = BillboardScraper("hot-100", date_list)
    scraper.scrape()

