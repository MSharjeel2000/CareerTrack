import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv("backend/.env")

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM goals")
rows = cursor.fetchall()
print(rows)
cursor.close()
connection.close()