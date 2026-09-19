import sqlite3

conn = sqlite3.connect('data/clinical.db')
conn.execute("UPDATE doctors SET full_name = 'Dr. Clinical AI' WHERE id = 1")
conn.commit()
print('Updated')
