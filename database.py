import mysql.connector
import os

def connectDatabase():
    """ MySQL 데이터베이스에 연결하고 커서를 반환합니다. """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except Exception as e:
        print(f"연결 오류: {e}")
        return None

def executeQuery(query):
    """ SQL 쿼리를 실행하는 함수입니다. """
    try:
        dbConnection = connectDatabase()
        if dbConnection:
            cursor = dbConnection.cursor()
            cursor.execute(query)
            dbConnection.commit()
            cursor.close()
            dbConnection.close()
    except Exception as e:
        print(f"쿼리 실행 오류: {e}")
