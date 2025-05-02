import sqlite3

# Create (or connect to) the database
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        time TEXT
    )
''')

conn.commit()
conn.close()
