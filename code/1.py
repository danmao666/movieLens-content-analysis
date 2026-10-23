from common import connect

conn = connect()
print(conn.sql("SHOW TABLES").df().to_string(index=False))
conn.close()