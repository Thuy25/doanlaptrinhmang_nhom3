import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=StockDB;'
    'Trusted_Connection=yes;'
)

cursor = conn.cursor()
cursor.execute("SELECT name FROM sys.tables")
for row in cursor.fetchall():
    print(row)