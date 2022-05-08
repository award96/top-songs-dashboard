
import pymysql

def get_credentials():
    aws_creds = {}
    with open("aws.txt", 'r') as file:
        for line in file:
            l, r = line.split("=")
            r = r.replace("\n", "")
            aws_creds[l] = r
    return aws_creds

def connect_aws():
    aws_creds = get_credentials()
    connection = pymysql.connect(host = aws_creds["AWS_DB_HOST"], 
        user = aws_creds["AWS_DB_USER"], 
        password = aws_creds["AWS_DB_PW"], 
        database = aws_creds["AWS_DB_DB"],
        port = int(aws_creds["AWS_DB_PORT"]))

    with connection:
        cur = connection.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()
        print("Database version: {} ".format(version[0]))

def select_aws(con, statement):
    pass


if __name__ == "__main__":
    connect_aws()