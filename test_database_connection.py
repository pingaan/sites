import os

import psycopg2


print(
    "Testing PostgreSQL connection:",
    os.environ["SITES_DB_HOST"],
    os.environ["SITES_DB_PORT"],
    os.environ["SITES_DB_NAME"],
    os.environ["SITES_DB_USER"],
)

connection = psycopg2.connect(
    host=os.environ["SITES_DB_HOST"],
    port=int(os.environ["SITES_DB_PORT"]),
    dbname=os.environ["SITES_DB_NAME"],
    user=os.environ["SITES_DB_USER"],
    password=os.environ["SITES_DB_PASSWORD"],
)

cursor = connection.cursor()

cursor.execute(
    "SELECT current_user, current_database()"
)

print(
    "PostgreSQL connection successful:",
    cursor.fetchone(),
)

cursor.close()
connection.close()