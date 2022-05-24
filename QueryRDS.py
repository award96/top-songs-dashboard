from rds_connect import get_credentials, query_aws, big_insert

class QueryRDS():
    """
    Streamlines use of AWS RDS MySQL database in Python
    """
    def __init__(self):
        self.creds = get_credentials()
        self.results = []
    
    def query(self, qstring, vals = None, isInsert = False):
        res = query_aws(qstring, self.creds, vals, isInsert)
        self.results.append(res)
        return res

    def bigInsert(self, qstring, vals):
        res = big_insert(qstring, vals, self.creds)
        return res

    def get_prev_queries(self, start_index = 0, stop_index = None):
        if stop_index is None:
            stop_index = len(self.results)
       
        return self.results[start_index:stop_index]
