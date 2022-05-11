
import pymysql

def get_credentials():
    """
        Reads aws.txt file and returns credentials dictionary
    """
    aws_creds = {}
    with open("aws.txt", 'r') as file:
        for line in file:
            l, r = line.split("=")
            r = r.replace("\n", "")
            aws_creds[l] = r
    return aws_creds

def _connect_aws(credentials = None):
    """
        Connects to MySQL database and returns connection object

        Do not import this method or use it outside of this module
        Why:    The connection object is not closed by this method
                It is always necessary to close the connection object, as done in the 
                query_aws method
    """
    if credentials is None:
        credentials = get_credentials()

    connection = pymysql.connect(host = credentials["AWS_DB_HOST"], 
        user = credentials["AWS_DB_USER"], 
        password = credentials["AWS_DB_PW"], 
        database = credentials["AWS_DB_DB"],
        port = int(credentials["AWS_DB_PORT"]))

    return connection

def query_aws(statement, credentials = None, vals = None, isInsert = False):
    """
        Executes MySQL query and returns results
    """
    
    connection = _connect_aws(credentials)

    if not connection.open:
        raise(ConnectionError)

    with connection:
        with connection.cursor() as cursor:
            if vals:
                cursor.execute(statement, vals)
            else:
                cursor.execute(statement)
            result = cursor.fetchall()
            cursor.close()
        if isInsert:
            connection.commit()
    return result