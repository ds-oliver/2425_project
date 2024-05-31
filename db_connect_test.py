import psycopg2
import pandas as pd

# Database connection parameters
db_params = {
    'dbname': 'project_db',
    'user': 'hogan',
    'password': 'Gunkis#1',
    'host': 'localhost',
    'port': '5432'
}

# set main() function
def main():
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("Database connection successful")
    except Exception as e:
        print("Database connection failed")
        print(e)

    # Close the database connection
    cursor.close()
    conn.close()
    print("Database connection closed")

# Call the main() function
if __name__ == '__main__':
    main()