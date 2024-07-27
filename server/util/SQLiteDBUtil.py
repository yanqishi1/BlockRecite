import sqlite3


class SQLiteDBUtil:
    def __init__(self,db):
        self.conn = sqlite3.connect(db)

    def query(self,sql):
        cursor = None
        try:
            print(sql)
            cursor = self.conn.cursor()
            cursor.execute(sql)
            db_result = cursor.fetchall()
            return db_result
        except Exception as e:
            raise e
        finally:
            if cursor is not None:
                cursor.close()
