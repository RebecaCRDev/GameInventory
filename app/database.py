from dotenv import load_dotenv, find_dotenv
import os
import mysql.connector
from typing import List, Dict, Any, cast
from mysql.connector.cursor import MySQLCursorDict  

# Carga .env desde la raíz
load_dotenv(find_dotenv())

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),        
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gameinventory"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset="utf8mb4"
    )