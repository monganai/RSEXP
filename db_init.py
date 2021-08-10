import psycopg2, os, datetime

creation_commands = (
    """
    CREATE TABLE users (
        user_id SERIAL PRIMARY KEY,
        user_name VARCHAR(255) NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL
    )
    """,
    """ CREATE TABLE crash_locations (
            location_id SERIAL PRIMARY KEY,
            location_latitude VARCHAR(255) NOT NULL,
            location_longitude VARCHAR(255) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL
            )
    """,
    """
    CREATE TABLE crash_data (
            crash_id SERIAL PRIMARY KEY,
            crash_gforce VARCHAR(255) NOT NULL,
            crash_rotational_velocity VARCHAR(255) NOT NULL,
            crash_classification VARCHAR(255) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL
            
    )
    """)

try:
    connect_str = "dbname='postgresdb' user='postgresadmin' host='192.168.0.230' port='30016'" + \
                  "password='admin123'"
    conn = psycopg2.connect(connect_str)
except Exception as e:
    print("Uh oh, can't connect. Invalid dbname, user or password?")
    print(e)

try:
    cursor = conn.cursor()
    for command in creation_commands:
        try:
            cursor.execute(command)
        except Exception as e:
            print("Table already exsists / can't create table: \n " + command + "\n")
    conn.commit()

except Exception as e:
    print("Unable to connect to the Database")
    print(e)

try:
    cursor.execute("""SELECT * from crash_data """)
    rows = cursor.fetchall()
except Exception as e:
    print("can't Query the Database")
    print(e)
        
if not rows:
    print("crash_data table is empty, loading data")
    basedir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(basedir, 'TrainingData.txt')
    with open(filepath) as fp:
        while fp.readline():
            line = fp.readline()
            list = line.split()
            ts = datetime.datetime.now().isoformat()
            cursor.execute('INSERT INTO crash_data (crash_gforce, crash_rotational_velocity, crash_classification, timestamp) VALUES(%s, %s, %s, %s)', (list[0], list[1], list[2], ts))
        conn.commit()
else:
    print("data is present, not inserting any data")


if conn is not None:
    conn.close()
