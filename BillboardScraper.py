import billboard


class BillboardScraper():
    def __init__(self, chart_name = "hot-100", date_list = []):
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
            self.output(chart, date)

    def output(self, chart, date):
        for song in chart:
            row = [song.title, 
                song.artist, 
                song.image, 
                song.peakPos, 
                song.lastPos,
                song.weeks,
                song.rank,
                song.isNew]


    @ property
    def date_list(self): return self._date_list.copy()

    @ property
    def chart_name(self): return self._chart_name
