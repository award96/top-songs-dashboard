import billboard
import datetime
from QueryRDS import QueryRDS


class BillboardScraper():
    def __init__(self, chart_name = "hot-100", date_list = [datetime.datetime.now().strftime("%Y-%m-%d")], verbose = True):
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
        self._missed_dates = []
        self.verbose = verbose
        self._rds = QueryRDS()

    def scrape(self):

        for date in self._date_list:
        
            try:
                chart = billboard.ChartData(self._chart_name, date)
            except:
                self._missed_dates.append(date)
                print(f"\nbillboard fetch request failed for {date}")
                continue


            if self.verbose:
                print(f"\n{len(chart)} songs found for {date}")
            self._output_RDS(chart, date)
            

    def _output_RDS(self, chart, date):
        all_rows = []
        for song in chart:
            row = (date,
                song.title, 
                song.artist, 
                song.image, 
                song.peakPos, 
                song.lastPos,
                song.weeks,
                song.rank,
                song.isNew)
            all_rows.append(row)

        is_duplicate = self._check_if_duplicate(date, len(all_rows))
        if not is_duplicate:
            self._insert_chart(all_rows)
            print(f"\nData inserted for date: {date}\n")
        else:
            print(f"Data likely already in DB for date: {date}\n")

    def _insert_chart(self, all_rows):
        query = "INSERT INTO charts (chart_date,title,artist,image,peakPos,lastPos,weeks,chart_rank,isNew) VALUES " + ",".join( 
            "(%s, %s, %s, %s, %s, %s, %s, %s, %s)" for _ in all_rows )

        # expression from https://softhints.com/insert-multiple-rows-at-once-with-python-and-mysql/
        vals = [item for sublist in all_rows for item in sublist]


        response = self._rds.query(query, vals, isInsert=True)
        if self.verbose:
            print(response)
            
    def _check_if_duplicate(self, date, numRows):
        query = f"SELECT chart_date FROM charts WHERE chart_date = '{date}'"
        res = self._rds.query(query)
        if len(res) > 0:
            if len(res) == numRows:
                print("\nExact row match for date already in table")
            return True
        return False

    @ property
    def date_list(self): return self._date_list.copy()

    @ property
    def chart_name(self): return self._chart_name

    @ property
    def rds(self): return self._rds

    @ property
    def missed_dates(self): return self._missed_dates.copy()
