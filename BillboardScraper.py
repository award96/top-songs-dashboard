import billboard
import datetime
from rds_connect import input_data


class BillboardScraper():
    def __init__(self, chart_name = "hot-100", date_list = [datetime.datetime.now().strftime("%Y-%m-%d")]):
        """
        ARGS:
            chart_name: a string representing which chart to download
                examples: 'hot-100', 'billboard-global-200'
                see all charts at https://www.billboard.com/charts/
            date_list: a list of strings. 
                Each string should be in the format 'YYYY-MM-DD'
        """
        self._chart_name = chart_name
        self._date_list = date_list

    def scrape(self):
        for date in self._date_list:
            chart = billboard.ChartData(self._chart_name, date)
            self._output_RDS(chart, date)

    def _output_RDS(self, chart, date):
        for song in chart:
            row = [date,
                song.title, 
                song.artist, 
                song.image, 
                song.peakPos, 
                song.lastPos,
                song.weeks,
                song.rank,
                song.isNew]
            self._input_row_rds(row)
    def _input_row_rds(self, row):
        pass


    @ property
    def date_list(self): return self._date_list.copy()

    @ property
    def chart_name(self): return self._chart_name
