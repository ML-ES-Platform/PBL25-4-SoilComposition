import psycopg2
from psycopg2 import sql
import sys
from config import DB_PARAMS

def create_database_and_table():
    # Database connection parameters
    db_params = DB_PARAMS
    
    database_name = db_params['database']
    
    try:
        conn = psycopg2.connect(database='postgres', **{k: v for k, v in db_params.items() if k != 'database'})
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{database_name}' already exists.")
        else:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
            print(f"Database '{database_name}' created successfully!")
        
        cursor.close()
        conn.close()
        
        # Now connect to the new database to create the table
        print(f"Connecting to '{database_name}' database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Create the moisture_data table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS moisture_data (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            moisture_value DECIMAL(5,2) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print("Table 'moisture_data' created successfully!")
        
        # Display table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'moisture_data'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\nTable structure:")
        print("-" * 60)
        print(f"{'Column':<15} {'Type':<15} {'Nullable':<10} {'Default':<15}")
        print("-" * 60)
        for col in columns:
            default_val = col[3] if col[3] else 'None'
            print(f"{col[0]:<15} {col[1]:<15} {col[2]:<10} {default_val:<15}")
        
        cursor.close()
        conn.close()
        
       
        
    except psycopg2.Error as e:
        sys.exit(1)
        
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    try:
        import psycopg2
    except ImportError:
        sys.exit(1)
    
    create_database_and_table()