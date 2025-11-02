# Database Migration Commands for Server

This document contains the commands to apply the database migrations on the server.

## Migration: Add Case Analysis History Table (011_add_case_analysis_history)

### Step 1: Backup Database (Recommended)
```bash
# Create a backup before migration
cp app.db app.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Check Current Migration Status
```bash
cd /path/to/legatoo_backend
alembic current
```

Expected output should show the current migration revision (e.g., `010` or `39aa74e45f8a`).

### Step 3: Apply Migration
```bash
# Option 1: Apply all pending migrations
alembic upgrade head

# Option 2: Apply specific migration
alembic upgrade 011_add_case_analysis_history
```

### Step 4: Verify Migration
```bash
# Check current migration status (should show 011_add_case_analysis_history)
alembic current

# Verify table exists
python3 -c "import sqlite3; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='case_analyses'\"); print('Table exists:', cursor.fetchone() is not None); conn.close()"
```

### If Migration Fails - Manual Table Creation

If the migration fails, you can create the table manually using this SQL:

```sql
CREATE TABLE IF NOT EXISTS case_analyses (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_size_mb FLOAT,
    analysis_type VARCHAR(50) NOT NULL,
    lawsuit_type VARCHAR(100) NOT NULL,
    result_seeking TEXT,
    user_context TEXT,
    analysis_data TEXT NOT NULL,  -- JSON stored as TEXT in SQLite
    risk_score INTEGER,
    risk_label VARCHAR(20),
    raw_response TEXT,
    additional_files TEXT,  -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_case_analyses_id ON case_analyses(id);
CREATE INDEX IF NOT EXISTS ix_case_analyses_user_id ON case_analyses(user_id);
CREATE INDEX IF NOT EXISTS ix_case_analyses_analysis_type ON case_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS ix_case_analyses_created_at ON case_analyses(created_at);
```

Then mark the migration as applied:
```bash
alembic stamp 011_add_case_analysis_history
```

### Troubleshooting

#### Multiple Heads Error
If you get "Multiple head revisions" error:
```bash
# Check heads
alembic heads

# If needed, merge heads or update down_revision in migration file
```

#### Table Already Exists
If table already exists but migration not marked:
```bash
# Stamp the migration as applied without running it
alembic stamp 011_add_case_analysis_history
```

#### Rollback Migration (if needed)
```bash
# Downgrade to previous migration
alembic downgrade 010

# Or downgrade by one step
alembic downgrade -1
```

## Installation Commands

### Install reportlab
```bash
pip install reportlab>=4.0.0

# Or update all requirements
pip install -r requirements.txt
```

## Verification

After migration, verify the system works:

1. **Check table structure:**
```bash
sqlite3 app.db ".schema case_analyses"
```

2. **Test analysis creation:**
- Upload a document through the API
- Check if analysis is saved to database

3. **Test PDF download:**
- Download an analysis PDF
- Verify PDF is generated correctly

