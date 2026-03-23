"""
Harbor - Configuration Module
Centralized configuration from environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ============================================
# Base Paths
# ============================================

BASE_DIR = Path(__file__).parent
DATABASE = os.environ.get('HARBOR_DATABASE', str(BASE_DIR / 'harbor.db'))
UPLOADS_DIR = os.environ.get('HARBOR_UPLOADS', str(BASE_DIR / 'uploads'))
LOGS_DIR = os.environ.get('HARBOR_LOGS', str(BASE_DIR / 'logs'))

# ============================================
# Server Settings
# ============================================

HOST = os.environ.get('HARBOR_HOST', '0.0.0.0')
PORT = int(os.environ.get('HARBOR_PORT', 5000))
DEBUG = os.environ.get('HARBOR_DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.environ.get('HARBOR_SECRET_KEY', 'dev-secret-change-in-production')

# ============================================
# Claude AI
# ============================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
AI_MODEL = os.environ.get('AI_MODEL', 'claude-sonnet-4-20250514')

# ============================================
# Zoom Integration
# ============================================

ZOOM_ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
ZOOM_CLIENT_ID = os.environ.get('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.environ.get('ZOOM_CLIENT_SECRET')

# ============================================
# Zoho Books Integration
# ============================================

ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID')
ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET')
ZOHO_ORG_ID = os.environ.get('ZOHO_ORG_ID')
ZOHO_REFRESH_TOKEN = os.environ.get('ZOHO_REFRESH_TOKEN')
ZOHO_REDIRECT_URI = os.environ.get('ZOHO_REDIRECT_URI', 'http://localhost:5000/auth/zoho/callback')

# ============================================
# Microsoft Integration
# ============================================

MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID')
MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/auth/microsoft/callback')

# ============================================
# File Watcher
# ============================================

FILE_INBOX = os.environ.get('HARBOR_INBOX', os.path.expanduser('~/Desktop/Harbor Inbox'))
CLIENT_FILES_ROOT = os.environ.get('HARBOR_CLIENT_FILES', str(BASE_DIR / 'uploads'))

# ============================================
# Timezone
# ============================================

TIMEZONE = os.environ.get('HARBOR_TIMEZONE', 'America/Chicago')

# ============================================
# Helper Functions
# ============================================

def is_configured(integration: str) -> bool:
    """Check if an integration has required credentials"""
    checks = {
        'claude': bool(ANTHROPIC_API_KEY),
        'zoom': all([ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET]),
        'zoho': all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORG_ID]),
        'microsoft': all([MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID]),
        'file_watcher': bool(FILE_INBOX and os.path.exists(FILE_INBOX)),
    }
    return checks.get(integration.lower(), False)

def get_all_status() -> dict:
    """Get configuration status for all integrations"""
    return {
        'claude': is_configured('claude'),
        'zoom': is_configured('zoom'),
        'zoho': is_configured('zoho'),
        'microsoft': is_configured('microsoft'),
        'file_watcher': is_configured('file_watcher'),
    }

def ensure_directories():
    """Create required directories if they don't exist"""
    Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    Path(UPLOADS_DIR + '/_unsorted').mkdir(parents=True, exist_ok=True)
    if FILE_INBOX:
        Path(FILE_INBOX).mkdir(parents=True, exist_ok=True)
