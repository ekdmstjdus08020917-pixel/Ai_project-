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

def executeQuery(query, params=None):
    """ SQL 쿼리를 실행하는 함수입니다. (파라미터 지원 추가) """
    try:
        dbConnection = connectDatabase()
        if dbConnection:
            cursor = dbConnection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            dbConnection.commit()
            cursor.close()
            dbConnection.close()
    except Exception as e:
        print(f"쿼리 실행 오류: {e}")

def createTable():
    """ 분석 결과를 저장할 테이블을 생성합니다. """
    query = """
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        prompt TEXT,
        model_name VARCHAR(50),
        result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    executeQuery(query)

def saveAnalysisResult(prompt, modelName, result):
    """ 분석 결과를 데이터베이스에 저장합니다. """
    query = "INSERT INTO analysis_results (prompt, model_name, result) VALUES (%s, %s, %s)"
    params = (prompt, modelName, result)
    executeQuery(query, params)
