"""
Harbor - Client Alias Management
Manage program names, abbreviations, and related organizations that map to clients.

This helps the file sorter recognize documents that refer to client programs
by other names (e.g. "Carmita's Kitchen" → Community Connect CDC).

Usage:
    python manage_aliases.py list                     List all aliases
    python manage_aliases.py add <client_id> <alias>  Add an alias
    python manage_aliases.py remove <alias_id>        Remove an alias
    python manage_aliases.py search <text>            Search for a match
    python manage_aliases.py setup                    Add initial known aliases
"""

import sys
import sqlite3
import config
import database as db


def ensure_table():
    """Create client_aliases table if it doesn't exist"""
    conn = db.get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS client_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            alias VARCHAR(200) NOT NULL,
            alias_type VARCHAR(50) DEFAULT 'program',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    conn.commit()
    conn.close()


def list_aliases():
    """List all aliases grouped by client"""
    aliases = db.get_all_aliases()
    if not aliases:
        print("No aliases configured yet.")
        print("Run: python manage_aliases.py setup")
        return
    
    current_client = None
    for a in aliases:
        if a['client_name'] != current_client:
            current_client = a['client_name']
            print(f"\n📂 {current_client}:")
        print(f"  [{a['id']}] \"{a['alias']}\" ({a['alias_type']})")


def add_alias(client_id: int, alias: str, alias_type: str = 'program', notes: str = None):
    """Add a new alias"""
    client = db.get_client_by_id(client_id)
    if not client:
        print(f"❌ Client ID {client_id} not found")
        return
    
    alias_id = db.add_alias(client_id, alias, alias_type, notes)
    print(f"✓ Added alias \"{alias}\" → {client['name']} (ID: {alias_id})")


def remove_alias(alias_id: int):
    """Remove an alias"""
    db.remove_alias(alias_id)
    print(f"✓ Removed alias #{alias_id}")


def search_alias(text: str):
    """Search for a client by alias"""
    client = db.find_client_by_alias(text)
    if client:
        print(f"✓ \"{text}\" → {client['name']} (ID: {client['id']})")
    else:
        print(f"✗ No alias match for \"{text}\"")


def setup_initial_aliases():
    """Add known aliases based on TSG's client relationships"""
    
    # Get all clients to map names to IDs
    clients = db.get_all_clients()
    client_map = {c['name']: c['id'] for c in clients}
    
    # Known aliases - add more as you discover them
    initial_aliases = []
    
    # Community Connect CDC aliases
    if 'Community Connect CDC' in client_map:
        cid = client_map['Community Connect CDC']
        initial_aliases.extend([
            (cid, "Carmita's Kitchen", "program", "Food/culinary program run by Community Connect CDC"),
            (cid, "Trinity Family Community Development Corporation", "related_org", "Church that houses Community Connect CDC"),
            (cid, "Trinity Family CDC", "related_org", "Short name for Trinity Family Community Development Corporation"),
            (cid, "Trinity Family", "related_org", "Short name"),
            (cid, "CCCDC", "abbreviation", None),
            (cid, "CCC", "abbreviation", None),
        ])
    
    # Baldwin ARC aliases
    if 'Baldwin ARC' in client_map:
        cid = client_map['Baldwin ARC']
        initial_aliases.extend([
            (cid, "ARC Baldwin County", "dba", "DBA / alternate name"),
            (cid, "ARC", "abbreviation", None),
        ])
    
    # Add them all
    added = 0
    for client_id, alias, alias_type, notes in initial_aliases:
        # Check if already exists
        existing = db.find_client_by_alias(alias)
        if not existing:
            db.add_alias(client_id, alias, alias_type, notes)
            client = db.get_client_by_id(client_id)
            print(f"  ✓ \"{alias}\" → {client['name']}")
            added += 1
        else:
            print(f"  ⏭ \"{alias}\" already exists")
    
    print(f"\n✅ Added {added} aliases")
    print("\nTo add more aliases:")
    print("  python manage_aliases.py add <client_id> \"Alias Name\"")


if __name__ == '__main__':
    ensure_table()
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'list':
        list_aliases()
    
    elif cmd == 'add' and len(sys.argv) >= 4:
        client_id = int(sys.argv[2])
        alias = sys.argv[3]
        alias_type = sys.argv[4] if len(sys.argv) > 4 else 'program'
        add_alias(client_id, alias, alias_type)
    
    elif cmd == 'remove' and len(sys.argv) >= 3:
        alias_id = int(sys.argv[2])
        remove_alias(alias_id)
    
    elif cmd == 'search' and len(sys.argv) >= 3:
        search_alias(sys.argv[2])
    
    elif cmd == 'setup':
        print("📝 Setting up initial client aliases...")
        setup_initial_aliases()
    
    else:
        print(__doc__)
