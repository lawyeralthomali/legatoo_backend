"""Script to create case_analyses table if it doesn't exist."""

import sqlite3
import os

# Database file path
db_path = "app.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='case_analyses'
    """)
    
    if cursor.fetchone() is None:
        print("Creating case_analyses table...")
        
        # Create table
        cursor.execute("""
            CREATE TABLE case_analyses (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename VARCHAR(500) NOT NULL,
                file_size_mb FLOAT,
                analysis_type VARCHAR(50) NOT NULL,
                lawsuit_type VARCHAR(100) NOT NULL,
                result_seeking TEXT,
                user_context TEXT,
                analysis_data TEXT NOT NULL,
                risk_score INTEGER,
                risk_label VARCHAR(20),
                raw_response TEXT,
                additional_files TEXT,
                created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                updated_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX ix_case_analyses_id ON case_analyses(id)")
        cursor.execute("CREATE INDEX ix_case_analyses_user_id ON case_analyses(user_id)")
        cursor.execute("CREATE INDEX ix_case_analyses_analysis_type ON case_analyses(analysis_type)")
        cursor.execute("CREATE INDEX ix_case_analyses_created_at ON case_analyses(created_at)")
        
        conn.commit()
        print("✅ case_analyses table created successfully!")
    else:
        print("✅ case_analyses table already exists!")
    
    conn.close()
else:
    print(f"⚠️  Database file {db_path} not found!")

