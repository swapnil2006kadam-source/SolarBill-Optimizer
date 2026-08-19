import os

DB_HOST = os.getenv("MYSQLHOST", "localhost")
DB_PORT = int(os.getenv("MYSQLPORT", "3306"))
DB_USER = os.getenv("MYSQLUSER", "root")
DB_PASSWORD = os.getenv("MYSQLPASSWORD", "steel1035")
DB_NAME = os.getenv("MYSQLDATABASE", "solar_bill_optimizer")

SECRET_KEY = os.getenv("SECRET_KEY", "solar_secret_key")