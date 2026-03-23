"""
Harbor - Database Utilities
"""

import sqlite3
from pathlib import Path
import config

def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query: str, args: tuple = (), one: bool = False):
    """Execute a query and return results"""
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query: str, args: tuple = ()) -> int:
    """Execute a query and return lastrowid"""
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid

def init_db():
    """Initialize database from schema.sql"""
    schema_path = Path(__file__).parent / 'schema.sql'
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    conn = get_db()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Database initialized: {config.DATABASE}")

def dict_from_row(row) -> dict:
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(row)

def rows_to_dicts(rows) -> list:
    """Convert list of sqlite3.Row to list of dicts"""
    return [dict_from_row(row) for row in rows]

# ============================================
# Client Functions
# ============================================

def get_all_clients(active_only: bool = True):
    """Get all clients"""
    query = 'SELECT * FROM clients'
    if active_only:
        query += ' WHERE status = "active"'
    query += ' ORDER BY name'
    return rows_to_dicts(query_db(query))

def get_client_by_code(code: str):
    """Get client by login code"""
    return dict_from_row(query_db(
        'SELECT * FROM clients WHERE code = ?', [code], one=True
    ))

def get_client_by_id(client_id: int):
    """Get client by ID"""
    return dict_from_row(query_db(
        'SELECT * FROM clients WHERE id = ?', [client_id], one=True
    ))

# ============================================
# Staff Functions
# ============================================

def get_staff_by_username(username: str):
    """Get staff member by username"""
    return dict_from_row(query_db(
        'SELECT * FROM staff WHERE username = ?', [username], one=True
    ))

def get_all_staff():
    """Get all staff members"""
    return rows_to_dicts(query_db('SELECT id, username, display_name, email, role FROM staff'))

# ============================================
# Activity Logging
# ============================================

def log_activity(action: str, description: str, client_id: int = None, 
                 entity_type: str = None, entity_id: int = None, 
                 performed_by: str = 'system'):
    """Log an activity"""
    execute_db('''
        INSERT INTO activity_log (client_id, action, entity_type, entity_id, description, performed_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [client_id, action, entity_type, entity_id, description, performed_by])

# ============================================
# Client Alias Functions
# ============================================

def get_all_aliases():
    """Get all client aliases with client info"""
    return rows_to_dicts(query_db('''
        SELECT ca.id, ca.client_id, ca.alias, ca.alias_type, ca.notes,
               c.name as client_name, c.short_name as client_short_name
        FROM client_aliases ca
        JOIN clients c ON ca.client_id = c.id
        WHERE c.status = 'active'
        ORDER BY c.name, ca.alias
    '''))

def get_aliases_for_client(client_id: int):
    """Get all aliases for a specific client"""
    return rows_to_dicts(query_db(
        'SELECT * FROM client_aliases WHERE client_id = ? ORDER BY alias',
        [client_id]
    ))

def add_alias(client_id: int, alias: str, alias_type: str = 'program', notes: str = None) -> int:
    """Add an alias for a client"""
    return execute_db('''
        INSERT INTO client_aliases (client_id, alias, alias_type, notes)
        VALUES (?, ?, ?, ?)
    ''', [client_id, alias, alias_type, notes])

def remove_alias(alias_id: int):
    """Remove an alias by ID"""
    execute_db('DELETE FROM client_aliases WHERE id = ?', [alias_id])

def find_client_by_alias(alias_text: str):
    """Search aliases for a matching client. Returns client dict or None."""
    result = query_db('''
        SELECT c.* FROM clients c
        JOIN client_aliases ca ON c.id = ca.client_id
        WHERE LOWER(ca.alias) = LOWER(?)
        AND c.status = 'active'
        LIMIT 1
    ''', [alias_text], one=True)
    return dict_from_row(result) if result else None


# ============================================
# Token Storage
# ============================================

def save_integration_token(service: str, access_token: str, refresh_token: str = None,
                           expires_at: str = None, extra_data: str = None):
    """Save or update an integration token"""
    conn = get_db()
    conn.execute('''
        INSERT INTO integration_tokens (service, access_token, refresh_token, expires_at, extra_data, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(service) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = COALESCE(excluded.refresh_token, refresh_token),
            expires_at = excluded.expires_at,
            extra_data = excluded.extra_data,
            updated_at = CURRENT_TIMESTAMP
    ''', [service, access_token, refresh_token, expires_at, extra_data])
    conn.commit()
    conn.close()

def get_integration_token(service: str):
    """Get stored token for a service"""
    return dict_from_row(query_db(
        'SELECT * FROM integration_tokens WHERE service = ?', [service], one=True
    ))

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
