import sqlite3
import pandas as pd

conn = sqlite3.connect("business.db")

print(pd.read_sql_query("SELECT * FROM Customers LIMIT 5;", conn))
print(pd.read_sql_query("SELECT * FROM Categories;", conn))
print(pd.read_sql_query("SELECT * FROM Products LIMIT 5;", conn))
print(pd.read_sql_query("SELECT * FROM Orders LIMIT 5;", conn))

conn.close()
