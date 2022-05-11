#import pymysql

#con = pymysql.connect(host="localhost", user="myuser", passwd="mypass", db="test")
#cursor = con.cursor()

values_to_insert = [(1, 2, 'a'), (3, 4, 'b'), (5, 6, 'c')]
query = "INSERT INTO tab (col1, col2, col3) VALUES " + ",".join("(%s, %s, %s)" for _ in values_to_insert)
flattened_values = [item for sublist in values_to_insert for item in sublist]
print(query)
print(f"\n{flattened_values}")
#cursor.execute(query, flattened_values)

#con.commit()