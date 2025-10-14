import pandas as pd
import sqlite3

# 1. Load your combined CSV
df = pd.read_csv("../dataset/combined_happiness.csv")

# 2. Connect (or create) a SQLite database file
conn = sqlite3.connect("happiness.db")

# 3. Write the DataFrame to a new table in the database
df.to_sql("happiness", conn, if_exists="replace", index=False)

# 4. Close the connection
conn.close()
