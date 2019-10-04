import irisnative
import pyodbc

def get_odbc_connection():
    ip = "localhost"
    port = 8082
    namespace = "USER"
    username = "_SYSTEM"
    password = "_SYSTEM"
    driver = "{InterSystems ODBC}"
    # Create connection to InterSystems IRIS
    connection_string = 'DRIVER={};SERVER={};PORT={};DATABASE={};UID={};PWD={}'\
        .format(driver, ip, port, namespace, username, password)
    print(connection_string)

    connection = pyodbc.connect(connection_string)
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')

    return connection

CONNECTION = get_odbc_connection()


def create_tables():
    global CONNECTION
    cursor = CONNECTION.cursor()
    cursor.execute("DROP TABLE webpages")
    CONNECTION.commit()
    cursor.execute("CREATE TABLE webpages(title VARCHAR(1024),url VARCHAR(1024),cleantext VARCHAR(4096),abstract VARCHAR(4096))")
    CONNECTION.commit()

def insert_webpage(title, url, cleantext, abstract):
    global CONNECTION
    cursor = CONNECTION.cursor()
    cursor.execute("""INSERT INTO webpages(title,url,cleantext,abstract) VALUES (?, ?, ?, ?)""", title.encode('utf-8'), url.encode('utf-8'), cleantext.encode('utf-8'), abstract.encode('utf-8'))
    CONNECTION.commit()

def retrive_webpage_by_title(title):
    global CONNECTION
    cursor = CONNECTION.cursor()

    rv = cursor.execute("SELECT * FROM webpages WHERE title = ?", title)
    return list(rv)


if __name__ == '__main__':
    create_tables()
