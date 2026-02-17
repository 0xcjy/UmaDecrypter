import apsw # SQL
import os

DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
DATA_PATH = "D:/app-data/umapd/Umamusume/umamusume_Data/Persistent"
CHARA_A = "1062_00"
CHARA_B = "1062_50"

if __name__ == "__main__":

    try:
        conn = apsw.Connection(os.path.join(DATA_PATH, "meta"), flags=apsw.SQLITE_OPEN_READWRITE)
        conn.pragma("hexkey", DB_KEY)
        cursor = conn.cursor()

        for col in ["n", "d"]:
            # Define the common WHERE clause for updates
            where_clause = f"({col} LIKE '%3d/chara/body/%' OR {col} LIKE '%3d/chara/head/%' OR {col} LIKE '%3d/chara/sweat/%')"

            # Step 1: Replace CHARA_A with a temporary string
            update_query_A_to_temp = f"UPDATE a SET {col} = REPLACE({col}, '{CHARA_A}', 'TEMP_{CHARA_A}_SWAP') WHERE {where_clause} AND {col} LIKE '%{CHARA_A}%'"
            cursor.execute(update_query_A_to_temp)
            print(f"Replaced '{CHARA_A}' with 'TEMP_{CHARA_A}_SWAP' for {conn.changes()} rows.")

            # Step 2: Replace CHARA_B with CHARA_A
            update_query_B_to_A = f"UPDATE a SET {col} = REPLACE({col}, '{CHARA_B}', '{CHARA_A}') WHERE {where_clause} AND {col} LIKE '%{CHARA_B}%'"
            cursor.execute(update_query_B_to_A)
            print(f"Replaced '{CHARA_B}' with '{CHARA_A}' for {conn.changes()} rows.")

            # Step 3: Replace the temporary string with CHARA_B
            update_query_temp_to_B = f"UPDATE a SET {col} = REPLACE({col}, 'TEMP_{CHARA_A}_SWAP', '{CHARA_B}') WHERE {where_clause} AND {col} LIKE '%TEMP_{CHARA_A}_SWAP%'"
            cursor.execute(update_query_temp_to_B)
            print(f"Replaced 'TEMP_{CHARA_A}_SWAP' with '{CHARA_B}' for {conn.changes()} rows.")

            print(f"\n{col} column replacement complete.")

            # Verification: Select and print some affected 'n' values
            print(f"\nVerifying some affected '{col}' values:")
            verification_query = f"SELECT n,d FROM a WHERE {where_clause} AND ({col} LIKE '%{CHARA_A}%' OR {col} LIKE '%{CHARA_B}%') LIMIT 10"
            for row in cursor.execute(verification_query):
                print(f"Verified n,d: {row[0]},{row[1]}")

        conn.close()

    except apsw.CantOpenError as e:
        print(f"Error: Unable to open database file. Please ensure the file is not locked and you have write permissions.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
