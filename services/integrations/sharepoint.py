"""
Harbor - Microsoft SharePoint Integration
Uses Microsoft Graph API for file management on SharePoint

This is the shared file storage for Harbor. Files are organized in:
  - Clients/[Client Name]/[Category]    (client project files)
  - Company/[Finance|Legal|HR|Admin]    (internal business docs)
  - Marketing/[Brand Assets|Website|Social Media|Proposals]
  - Resources/[Templates|Training|Reference]
  - Archive/                             (completed/old projects)
  - Harbor Inbox/                           (file drop zone for auto-sorting)

SharePoint Site: https://scanland.sharepoint.com/sites/TheScanlandGroup

SETUP:
1. Ensure MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID 
   are set in .env (from Azure App Registration)
2. Azure App needs these API permissions:
   - Files.ReadWrite.All
   - Sites.ReadWrite.All
   - User.Read
   - offline_access
3. Run: python integrations/sharepoint.py auth
4. Test: python integrations/sharepoint.py test
5. Setup folders: python integrations/sharepoint.py setup
"""

import os
import sys
import json
import time
import webbrowser
import logging
from urllib.parse import urlencode, quote
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import config
import database as db

logger = logging.getLogger('integration.sharepoint')

# SharePoint site configuration
SHAREPOINT_HOSTNAME = "scanland.sharepoint.com"
SHAREPOINT_SITE_PATH = "/sites/TheScanlandGroup"
DOCUMENT_LIBRARY = "Shared Documents"  # Default document library name


class SharePointClient:
    """Microsoft SharePoint client using Graph API"""
    
    # Microsoft identity endpoints
    AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    
    # Scopes needed for SharePoint file access
    SCOPES = [
        "Files.ReadWrite.All",
        "Sites.ReadWrite.All",
        "User.Read",
        "offline_access"
    ]
    
    def __init__(self):
        self.client_id = config.MICROSOFT_CLIENT_ID
        self.client_secret = config.MICROSOFT_CLIENT_SECRET
        self.tenant_id = config.MICROSOFT_TENANT_ID or "common"
        self.redirect_uri = config.MICROSOFT_REDIRECT_URI
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.site_id = None
        self.drive_id = None
    
    # ============ Authentication ============
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.SCOPES),
            "response_mode": "query",
            "prompt": "consent"
        }
        url = self.AUTH_URL.format(tenant=self.tenant_id)
        return f"{url}?{urlencode(params)}"
    
    def exchange_code(self, auth_code: str) -> bool:
        """Exchange authorization code for tokens"""
        url = self.TOKEN_URL.format(tenant=self.tenant_id)
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(self.SCOPES)
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Save token to database
            self._save_token()
            
            # Get site and drive info
            self._resolve_site()
            
            return True
        else:
            print(f"Token exchange failed: {response.text}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return False
        
        url = self.TOKEN_URL.format(tenant=self.tenant_id)
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(self.SCOPES)
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            if tokens.get("refresh_token"):
                self.refresh_token = tokens["refresh_token"]
            expires_in = tokens.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._save_token()
            return True
        else:
            logger.warning(f"Token refresh failed: {response.text}")
            return False
    
    def _save_token(self):
        """Save tokens to database"""
        extra = json.dumps({
            "site_id": self.site_id,
            "drive_id": self.drive_id
        })
        db.save_integration_token(
            service="sharepoint",
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_at=self.token_expires_at.isoformat() if self.token_expires_at else None,
            extra_data=extra
        )
    
    def load_token(self) -> bool:
        """Load tokens from database"""
        token_data = db.get_integration_token("sharepoint")
        if not token_data:
            return False
        
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")
        
        if token_data.get("expires_at"):
            try:
                self.token_expires_at = datetime.fromisoformat(token_data["expires_at"])
            except:
                self.token_expires_at = None
        
        # Load site/drive info
        if token_data.get("extra_data"):
            try:
                extra = json.loads(token_data["extra_data"])
                self.site_id = extra.get("site_id")
                self.drive_id = extra.get("drive_id")
            except:
                pass
        
        # Check if token is expired and refresh if needed
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            if not self.refresh_access_token():
                return False
        
        # Resolve site if we don't have it yet
        if not self.site_id:
            self._resolve_site()
        
        return True
    
    def _get_headers(self) -> dict:
        """Get authorization headers, refreshing token if needed"""
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self.refresh_access_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    # ============ Site & Drive Resolution ============
    
    def _resolve_site(self):
        """Get the SharePoint site ID and default drive ID"""
        try:
            # Get site by hostname and path
            url = f"{self.GRAPH_URL}/sites/{SHAREPOINT_HOSTNAME}:{SHAREPOINT_SITE_PATH}"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                site = response.json()
                self.site_id = site["id"]
                logger.info(f"Resolved site ID: {self.site_id}")
                
                # Get the default document library drive
                drives_url = f"{self.GRAPH_URL}/sites/{self.site_id}/drives"
                drives_response = requests.get(drives_url, headers=self._get_headers())
                
                if drives_response.status_code == 200:
                    drives = drives_response.json().get("value", [])
                    # Find the "Documents" drive (default library)
                    for drive in drives:
                        if drive.get("name") == "Documents" or drive.get("name") == DOCUMENT_LIBRARY:
                            self.drive_id = drive["id"]
                            logger.info(f"Resolved drive ID: {self.drive_id}")
                            break
                    
                    # If not found by name, use the first drive
                    if not self.drive_id and drives:
                        self.drive_id = drives[0]["id"]
                        logger.info(f"Using first drive: {self.drive_id}")
                
                # Save updated IDs
                self._save_token()
            else:
                logger.warning(f"Failed to resolve site: {response.text}")
        except Exception as e:
            logger.warning(f"Site resolution failed: {e}")
    
    # ============ File Operations ============
    
    def create_folder(self, folder_name: str, parent_path: str = "") -> dict:
        """Create a folder in SharePoint"""
        if not self.drive_id:
            self._resolve_site()
        
        if parent_path:
            url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{parent_path}:/children"
        else:
            url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root/children"
        
        data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"  # Don't create duplicates
        }
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        
        if response.status_code in [200, 201]:
            logger.info(f"Created folder: {parent_path}/{folder_name}")
            return response.json()
        elif response.status_code == 409:
            # Folder already exists - that's fine
            logger.info(f"Folder already exists: {parent_path}/{folder_name}")
            return {"name": folder_name, "exists": True}
        else:
            logger.warning(f"Failed to create folder {parent_path}/{folder_name}: {response.text}")
            return None
    
    def upload_file(self, local_path: str, sharepoint_path: str) -> dict:
        """
        Upload a file to SharePoint.
        
        Args:
            local_path: Path to local file
            sharepoint_path: Destination path in SharePoint (e.g. "Clients/ARC/Reports/file.pdf")
        
        Returns: File metadata dict or None on failure
        """
        if not self.drive_id:
            self._resolve_site()
        
        file_size = os.path.getsize(local_path)
        
        # For files under 4MB, use simple upload
        if file_size < 4 * 1024 * 1024:
            return self._simple_upload(local_path, sharepoint_path)
        else:
            return self._chunked_upload(local_path, sharepoint_path)
    
    def _simple_upload(self, local_path: str, sharepoint_path: str) -> dict:
        """Upload a small file (< 4MB) using simple PUT"""
        url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{sharepoint_path}:/content"
        
        with open(local_path, 'rb') as f:
            headers = self._get_headers()
            headers["Content-Type"] = "application/octet-stream"
            
            response = requests.put(url, headers=headers, data=f)
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"Uploaded: {sharepoint_path}")
            return result
        else:
            logger.warning(f"Upload failed for {sharepoint_path}: {response.text}")
            return None
    
    def _chunked_upload(self, local_path: str, sharepoint_path: str) -> dict:
        """Upload a large file using upload session (chunked)"""
        # Create upload session
        url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{sharepoint_path}:/createUploadSession"
        
        session_data = {
            "item": {
                "@microsoft.graph.conflictBehavior": "rename",
                "name": os.path.basename(local_path)
            }
        }
        
        response = requests.post(url, headers=self._get_headers(), json=session_data)
        
        if response.status_code not in [200, 201]:
            logger.warning(f"Failed to create upload session: {response.text}")
            return None
        
        upload_url = response.json()["uploadUrl"]
        file_size = os.path.getsize(local_path)
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        
        with open(local_path, 'rb') as f:
            chunk_start = 0
            while chunk_start < file_size:
                chunk_end = min(chunk_start + chunk_size, file_size) - 1
                chunk_data = f.read(chunk_size)
                
                headers = {
                    "Content-Length": str(len(chunk_data)),
                    "Content-Range": f"bytes {chunk_start}-{chunk_end}/{file_size}"
                }
                
                chunk_response = requests.put(upload_url, headers=headers, data=chunk_data)
                
                if chunk_response.status_code in [200, 201]:
                    logger.info(f"Upload complete: {sharepoint_path}")
                    return chunk_response.json()
                elif chunk_response.status_code == 202:
                    # Chunk accepted, continue
                    chunk_start = chunk_end + 1
                else:
                    logger.warning(f"Chunk upload failed: {chunk_response.text}")
                    return None
        
        return None
    
    def list_folder(self, folder_path: str = "") -> list:
        """List contents of a folder"""
        if not self.drive_id:
            self._resolve_site()
        
        if folder_path:
            url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{folder_path}:/children"
        else:
            url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root/children"
        
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            logger.warning(f"Failed to list folder {folder_path}: {response.text}")
            return []
    
    def get_file_url(self, file_path: str) -> str:
        """Get the web URL for a file"""
        if not self.drive_id:
            self._resolve_site()
        
        url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{file_path}"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json().get("webUrl")
        return None
    
    def create_sharing_link(self, file_path: str, link_type: str = "view") -> str:
        """Create a sharing link for a file"""
        if not self.drive_id:
            self._resolve_site()
        
        url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{file_path}:/createLink"
        data = {
            "type": link_type,
            "scope": "organization"
        }
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        
        if response.status_code in [200, 201]:
            return response.json().get("link", {}).get("webUrl")
        else:
            logger.warning(f"Failed to create link: {response.text}")
            return None
    
    def move_item(self, item_path: str, new_parent_path: str) -> dict:
        """
        Move a file or folder to a new parent folder.
        
        Args:
            item_path: Current path (e.g. "Clients")
            new_parent_path: New parent folder path (e.g. "The Scanland Group")
        """
        if not self.drive_id:
            self._resolve_site()
        
        # Get the item ID
        item_url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{item_path}"
        item_response = requests.get(item_url, headers=self._get_headers())
        
        if item_response.status_code != 200:
            logger.warning(f"Item not found: {item_path}")
            return None
        
        item_id = item_response.json()["id"]
        
        # Get the destination parent ID
        if new_parent_path:
            parent_url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root:/{new_parent_path}"
        else:
            parent_url = f"{self.GRAPH_URL}/drives/{self.drive_id}/root"
        
        parent_response = requests.get(parent_url, headers=self._get_headers())
        
        if parent_response.status_code != 200:
            logger.warning(f"Destination not found: {new_parent_path}")
            return None
        
        parent_id = parent_response.json()["id"]
        
        # Move the item
        move_url = f"{self.GRAPH_URL}/drives/{self.drive_id}/items/{item_id}"
        move_data = {
            "parentReference": {
                "id": parent_id
            }
        }
        
        move_response = requests.patch(move_url, headers=self._get_headers(), json=move_data)
        
        if move_response.status_code == 200:
            logger.info(f"Moved: {item_path} → {new_parent_path}/")
            return move_response.json()
        else:
            logger.warning(f"Move failed for {item_path}: {move_response.text}")
            return None
    
    # ============ Harbor-Specific Operations ============
    
    def setup_harbor_structure(self):
        """Create the complete Scanland & Co folder structure in SharePoint"""
        print("\n📁 Setting up Scanland & Co folder structure in SharePoint...")
        
        structure = {
            "Scanland & Co": [
                "Finance",
                "Legal",
                "Admin",
                "Operations"
            ],
            "The Scanland Group": {
                "Clients": {
                    "_Templates": [
                        "Meeting Notes",
                        "Contracts",
                        "Proposals",
                        "Reports",
                        "Financials",
                        "Correspondence",
                        "_NeedsFolder"
                    ]
                },
                "Company": [
                    "Finance",
                    "Legal",
                    "HR",
                    "Admin"
                ],
                "Marketing": [
                    "Brand Assets",
                    "Website",
                    "Social Media",
                    "Proposals"
                ],
                "Resources": [
                    "Templates",
                    "Training",
                    "Reference"
                ],
                "Archive": []
            },
            "Harbor Inbox": []
        }
        
        def create_structure(base_path, items):
            if isinstance(items, dict):
                for folder, subfolders in items.items():
                    path = f"{base_path}/{folder}" if base_path else folder
                    result = self.create_folder(folder, base_path)
                    status = "✓" if result else "✗"
                    print(f"  {status} {path}/")
                    create_structure(path, subfolders)
            elif isinstance(items, list):
                for folder in items:
                    path = f"{base_path}/{folder}" if base_path else folder
                    result = self.create_folder(folder, base_path)
                    status = "✓" if result else "✗"
                    print(f"  {status} {path}/")
        
        create_structure("", structure)
        print("\n✅ Scanland & Co folder structure created!")
    
    def restructure_for_scanland_co(self):
        """
        Migrate existing flat TSG structure into nested Scanland & Co structure.
        
        Moves:
          Clients/     → The Scanland Group/Clients/
          Company/     → The Scanland Group/Company/
          Marketing/   → The Scanland Group/Marketing/
          Resources/   → The Scanland Group/Resources/
          Archive/     → The Scanland Group/Archive/
        
        Creates:
          Scanland & Co/  (with Finance/, Legal/, Admin/, Operations/)
          The Scanland Group/  (as container for moved folders)
        
        Leaves at root:
          Harbor Inbox/  (or creates it if TSG Inbox exists)
        """
        print("\n🔄 Restructuring SharePoint for Scanland & Co...")
        print("   This will move existing TSG folders under 'The Scanland Group/'")
        print()
        
        # Step 1: Create new top-level folders
        print("Step 1: Creating top-level folders...")
        self.create_folder("Scanland & Co", "")
        for sub in ["Finance", "Legal", "Admin", "Operations"]:
            self.create_folder(sub, "Scanland & Co")
            print(f"  ✓ Scanland & Co/{sub}/")
        
        self.create_folder("The Scanland Group", "")
        print(f"  ✓ The Scanland Group/")
        
        # Rename TSG Inbox to Harbor Inbox if it exists
        # (We can't rename via API easily, so just create Harbor Inbox)
        self.create_folder("Harbor Inbox", "")
        print(f"  ✓ Harbor Inbox/")
        
        # Step 2: Move existing folders into The Scanland Group
        print("\nStep 2: Moving existing folders...")
        folders_to_move = ["Clients", "Company", "Marketing", "Resources", "Archive"]
        
        for folder_name in folders_to_move:
            print(f"  Moving {folder_name}/ → The Scanland Group/{folder_name}/...", end=" ")
            result = self.move_item(folder_name, "The Scanland Group")
            if result:
                print("✓")
            else:
                print("⚠ (may not exist or already moved)")
        
        print("\n✅ Restructure complete!")
        print("\nNew structure:")
        print("  📁 Scanland & Co/")
        print("  │   ├── Finance/")
        print("  │   ├── Legal/")
        print("  │   ├── Admin/")
        print("  │   └── Operations/")
        print("  📁 The Scanland Group/")
        print("  │   ├── Clients/")
        print("  │   ├── Company/")
        print("  │   ├── Marketing/")
        print("  │   ├── Resources/")
        print("  │   └── Archive/")
        print("  📁 Harbor Inbox/")
        print("\n⚠  You can delete the old 'TSG Inbox' folder in SharePoint if it's empty.")
    
    def create_client_folder(self, client_name: str, subsidiary: str = "The Scanland Group"):
        """Create a client folder with standard subfolders"""
        base_path = f"{subsidiary}/Clients"
        print(f"\n📂 Creating client folder: {base_path}/{client_name}")
        
        # Create the main client folder
        result = self.create_folder(client_name, base_path)
        if result:
            print(f"  ✓ {base_path}/{client_name}/")
        
        # Create subfolders
        subfolders = [
            "Meeting Notes",
            "Contracts",
            "Proposals",
            "Reports",
            "Financials",
            "Correspondence",
            "_NeedsFolder"
        ]
        
        client_path = f"{base_path}/{client_name}"
        for subfolder in subfolders:
            result = self.create_folder(subfolder, client_path)
            status = "✓" if result else "✗"
            print(f"  {status} {client_path}/{subfolder}/")
        
        print(f"  ✅ Done!")
    
    def create_all_client_folders(self):
        """Create folders for all active clients in the database"""
        clients = db.get_all_clients()
        
        if not clients:
            print("No clients found in database")
            return
        
        print(f"\n📂 Creating folders for {len(clients)} clients...")
        
        for client in clients:
            self.create_client_folder(client['name'])
        
        print(f"\n✅ All {len(clients)} client folders created!")
    
    def test_connection(self) -> tuple:
        """Test SharePoint connection. Returns (success, message)"""
        if not self.access_token:
            if not self.load_token():
                return False, "Not authenticated. Run: python integrations/sharepoint.py auth"
        
        try:
            # Test by getting user info
            response = requests.get(
                f"{self.GRAPH_URL}/me",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                user = response.json()
                user_name = user.get("displayName", "Unknown")
                
                # Test site access
                site_url = f"{self.GRAPH_URL}/sites/{SHAREPOINT_HOSTNAME}:{SHAREPOINT_SITE_PATH}"
                site_response = requests.get(site_url, headers=self._get_headers())
                
                if site_response.status_code == 200:
                    site = site_response.json()
                    site_name = site.get("displayName", "Unknown")
                    
                    # List root folders
                    items = self.list_folder("")
                    folder_names = [i["name"] for i in items if i.get("folder")]
                    
                    return True, (
                        f"Connected as: {user_name}\n"
                        f"  Site: {site_name}\n"
                        f"  Site ID: {self.site_id}\n"
                        f"  Drive ID: {self.drive_id}\n"
                        f"  Root folders: {', '.join(folder_names)}"
                    )
                else:
                    return False, f"Cannot access SharePoint site: {site_response.status_code}"
            else:
                return False, f"Auth test failed: {response.status_code}"
        except Exception as e:
            return False, f"Connection error: {e}"


# ============================================
# OAuth Callback Handler
# ============================================

_auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    
    def do_GET(self):
        global _auth_code
        
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            _auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2 style="color: green;">&#10004; Authentication Successful!</h2>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        elif 'error' in query:
            error = query.get('error_description', query.get('error', ['Unknown error']))
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2 style="color: red;">&#10008; Authentication Failed</h2>
                <p>{error[0] if isinstance(error, list) else error}</p>
                </body></html>
            """.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress log output


def authenticate_interactive():
    """Run interactive OAuth flow"""
    global _auth_code
    _auth_code = None
    
    sp = SharePointClient()
    
    if not sp.client_id or not sp.client_secret:
        print("❌ MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set in .env")
        return
    
    auth_url = sp.get_auth_url()
    
    # Start callback server
    server = HTTPServer(('localhost', 5000), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()
    
    print("\n🔐 Opening browser for Microsoft authentication...")
    print(f"   If the browser doesn't open, go to:\n   {auth_url}\n")
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("   Waiting for authentication...")
    server_thread.join(timeout=120)
    server.server_close()
    
    if _auth_code:
        print("   Exchanging code for tokens...")
        if sp.exchange_code(_auth_code):
            success, msg = sp.test_connection()
            if success:
                print(f"\n✅ SharePoint authenticated!")
                print(f"   {msg}")
            else:
                print(f"\n⚠ Authenticated but site access issue: {msg}")
        else:
            print("\n❌ Token exchange failed")
    else:
        print("\n❌ No authorization code received (timeout or error)")


# ============================================
# CLI
# ============================================

if __name__ == '__main__':
    def print_usage():
        print("""
SharePoint Integration CLI

Commands:
    auth                Interactive OAuth authentication
    test                Test connection
    setup               Create full Harbor folder structure
    clients             Create all client folders
    client <name>       Create a single client folder
    list [path]         List folder contents
    upload <file> <sp_path>  Upload a file
    
Examples:
    python integrations/sharepoint.py auth
    python integrations/sharepoint.py test
    python integrations/sharepoint.py setup
    python integrations/sharepoint.py clients
    python integrations/sharepoint.py client "New Client Name"
    python integrations/sharepoint.py list Clients
    python integrations/sharepoint.py upload ~/Downloads/report.pdf "Clients/ARC/Reports/report.pdf"
""")
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'auth':
        authenticate_interactive()
    
    elif cmd == 'test':
        sp = SharePointClient()
        success, msg = sp.test_connection()
        print(f"{'✓' if success else '✗'} SharePoint Status:")
        print(f"  {msg}")
    
    elif cmd == 'setup':
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        sp.setup_harbor_structure()
    
    elif cmd == 'restructure':
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        sp.restructure_for_scanland_co()
    
    elif cmd == 'clients':
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        sp.create_all_client_folders()
    
    elif cmd == 'client' and len(sys.argv) > 2:
        client_name = sys.argv[2]
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        sp.create_client_folder(client_name)
    
    elif cmd == 'list':
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        folder_path = sys.argv[2] if len(sys.argv) > 2 else ""
        items = sp.list_folder(folder_path)
        
        if items:
            path_display = folder_path or "(root)"
            print(f"\n📂 {path_display}:")
            for item in items:
                icon = "📁" if item.get("folder") else "📄"
                size = item.get("size", 0)
                modified = item.get("lastModifiedDateTime", "")[:10]
                print(f"  {icon} {item['name']:<40} {modified}  {size:>10,} bytes")
        else:
            print("No items found (or folder doesn't exist)")
    
    elif cmd == 'upload' and len(sys.argv) > 3:
        local_path = sys.argv[2]
        sp_path = sys.argv[3]
        sp = SharePointClient()
        if not sp.load_token():
            print("❌ Not authenticated. Run: python integrations/sharepoint.py auth")
            sys.exit(1)
        
        if os.path.isfile(local_path):
            result = sp.upload_file(local_path, sp_path)
            if result:
                print(f"✓ Uploaded to: {sp_path}")
                print(f"  URL: {result.get('webUrl', 'N/A')}")
            else:
                print(f"✗ Upload failed")
        else:
            print(f"File not found: {local_path}")
    
    else:
        print(f"Unknown command: {cmd}")
        print_usage()
