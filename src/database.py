import pymysql

class Database:
    # Singleton to manage DB interaction
    
    conn = pymysql.connect(host='localhost', user='root', db='cookzilla', charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    
    @classmethod
    def query(cls, query_string):
        cursor = cls.conn.cursor()
        cursor.execute(query_string)
        data = cursor.fetchall()
        return data
    
    @classmethod
    def query_one(cls, query_string):
        cursor = cls.conn.cursor()
        cursor.execute(query_string)
        data = cursor.fetchone()
        return data
    
    @classmethod
    def insert(cls, insert_string):
        cursor = cls.conn.cursor()
        cursor.execute(insert_string)
        cls.conn.commit()
    
    