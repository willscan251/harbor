"""
Harbor - Zoho Books Integration
Handles invoices and customer sync

SETUP:
1. Go to https://api-console.zoho.com/
2. Add Client → Server-based Applications
3. Name: "Harbor"
4. Redirect URI: http://localhost:5000/auth/zoho/callback
5. Copy Client ID and Client Secret to .env
6. Get Organization ID from Zoho Books → Settings → Organization
7. Run: python integrations/zoho.py auth (to get refresh token)
"""

import logging
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import urlencode

import requests

import config
import database as db

logger = logging.getLogger('integration.zoho')

class ZohoIntegration:
    """Zoho Books API integration"""
    
    def __init__(self):
        self.access_token = None
        self.token_expires_at = None
        self.base_url = 'https://www.zohoapis.com/books/v3'
        self.auth_url = 'https://accounts.zoho.com/oauth/v2'
    
    def is_configured(self) -> bool:
        """Check if Zoho credentials are configured"""
        return config.is_configured('zoho')
    
    def _refresh_access_token(self) -> str:
        """Get a new access token using the refresh token"""
        if not config.ZOHO_REFRESH_TOKEN:
            raise RuntimeError("ZOHO_REFRESH_TOKEN not configured. Run: python integrations/zoho.py auth")
        
        response = requests.post(
            f'{self.auth_url}/token',
            data={
                'refresh_token': config.ZOHO_REFRESH_TOKEN,
                'client_id': config.ZOHO_CLIENT_ID,
                'client_secret': config.ZOHO_CLIENT_SECRET,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.token_expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))
            logger.info("Zoho access token refreshed")
            return self.access_token
        else:
            logger.error(f"Zoho token refresh failed: {response.text}")
            raise RuntimeError(f"Zoho token refresh failed: {response.text}")
    
    def _get_access_token(self) -> str:
        """Get a valid access token"""
        # Check stored token first
        stored = db.get_integration_token('zoho')
        if stored and stored.get('access_token'):
            expires = stored.get('expires_at')
            if expires:
                expires_dt = datetime.fromisoformat(expires) if isinstance(expires, str) else expires
                if datetime.now() < expires_dt - timedelta(minutes=5):
                    self.access_token = stored['access_token']
                    return self.access_token
        
        # Check in-memory token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return self.access_token
        
        # Refresh token
        token = self._refresh_access_token()
        
        # Store for persistence
        db.save_integration_token(
            service='zoho',
            access_token=token,
            expires_at=self.token_expires_at.isoformat() if self.token_expires_at else None
        )
        
        return token
    
    def _api_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make an authenticated API request"""
        token = self._get_access_token()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Content-Type': 'application/json'
        }
        
        # Always include organization_id
        base_params = {'organization_id': config.ZOHO_ORG_ID}
        if params:
            base_params.update(params)
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=base_params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=base_params, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, params=base_params, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=base_params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        result = response.json()
        
        if result.get('code') == 0:
            return result
        else:
            error_msg = result.get('message', 'Unknown error')
            logger.error(f"Zoho API error: {error_msg}")
            raise RuntimeError(f"Zoho API error: {error_msg}")
    
    def test_connection(self) -> tuple:
        """Test Zoho connection. Returns (success, message)"""
        if not self.is_configured():
            return False, "Zoho credentials not configured in .env"
        
        if not config.ZOHO_REFRESH_TOKEN:
            return False, "ZOHO_REFRESH_TOKEN not set. Run: python integrations/zoho.py auth"
        
        try:
            result = self._api_request('GET', '/invoices', params={'per_page': 1})
            return True, "Connected to Zoho Books!"
        except Exception as e:
            return False, str(e)
    
    # ============================================
    # OAuth Flow (for initial setup)
    # ============================================
    
    def get_auth_url(self) -> str:
        """Get the OAuth authorization URL"""
        params = {
            'client_id': config.ZOHO_CLIENT_ID,
            'redirect_uri': config.ZOHO_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'ZohoBooks.fullaccess.all',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"{self.auth_url}/auth?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for tokens"""
        response = requests.post(
            f'{self.auth_url}/token',
            data={
                'code': code,
                'client_id': config.ZOHO_CLIENT_ID,
                'client_secret': config.ZOHO_CLIENT_SECRET,
                'redirect_uri': config.ZOHO_REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Store tokens
            db.save_integration_token(
                service='zoho',
                access_token=data.get('access_token'),
                refresh_token=data.get('refresh_token'),
                expires_at=(datetime.now() + timedelta(seconds=data.get('expires_in', 3600))).isoformat()
            )
            
            return data
        else:
            raise RuntimeError(f"Token exchange failed: {response.text}")
    
    # ============================================
    # Customers (Contacts)
    # ============================================
    
    def get_customers(self) -> List[dict]:
        """Get all customers from Zoho Books"""
        result = self._api_request('GET', '/contacts', params={
            'contact_type': 'customer',
            'per_page': 200
        })
        return result.get('contacts', [])
    
    def get_customer(self, customer_id: str) -> dict:
        """Get a specific customer"""
        result = self._api_request('GET', f'/contacts/{customer_id}')
        return result.get('contact', {})
    
    def create_customer(self, name: str, email: str = None, phone: str = None) -> dict:
        """Create a new customer in Zoho Books"""
        data = {
            'contact_name': name,
            'contact_type': 'customer'
        }
        if email:
            data['email'] = email
        if phone:
            data['phone'] = phone
        
        result = self._api_request('POST', '/contacts', data=data)
        return result.get('contact', {})
    
    def find_customer_by_name(self, name: str) -> Optional[dict]:
        """Find a customer by name (partial match)"""
        result = self._api_request('GET', '/contacts', params={
            'contact_type': 'customer',
            'search_text': name
        })
        contacts = result.get('contacts', [])
        return contacts[0] if contacts else None
    
    # ============================================
    # Invoices
    # ============================================
    
    def get_invoices(self, status: str = None, customer_id: str = None) -> List[dict]:
        """
        Get invoices, optionally filtered
        
        Status options: draft, sent, overdue, paid, void, unpaid, partially_paid
        """
        params = {'per_page': 200}
        if status:
            params['status'] = status
        if customer_id:
            params['customer_id'] = customer_id
        
        result = self._api_request('GET', '/invoices', params=params)
        return result.get('invoices', [])
    
    def get_invoice(self, invoice_id: str) -> dict:
        """Get a specific invoice"""
        result = self._api_request('GET', f'/invoices/{invoice_id}')
        return result.get('invoice', {})
    
    def create_invoice(self, customer_id: str, line_items: List[dict], 
                       due_date: str = None, notes: str = None) -> dict:
        """
        Create a new invoice
        
        Args:
            customer_id: Zoho customer ID
            line_items: List of items, each with:
                        {'description': str, 'rate': float, 'quantity': float}
            due_date: Optional due date (YYYY-MM-DD)
            notes: Optional notes
        
        Returns:
            Created invoice
        """
        invoice_data = {
            'customer_id': customer_id,
            'line_items': [
                {
                    'description': item['description'],
                    'rate': item['rate'],
                    'quantity': item.get('quantity', 1)
                }
                for item in line_items
            ]
        }
        
        if due_date:
            invoice_data['due_date'] = due_date
        if notes:
            invoice_data['notes'] = notes
        
        result = self._api_request('POST', '/invoices', data=invoice_data)
        return result.get('invoice', {})
    
    def send_invoice(self, invoice_id: str, email_to: str = None) -> bool:
        """Send an invoice via email"""
        data = {}
        if email_to:
            data['send_to_list'] = [{'email_address': email_to}]
        
        try:
            self._api_request('POST', f'/invoices/{invoice_id}/email', data=data)
            return True
        except:
            return False
    
    def mark_invoice_paid(self, invoice_id: str, amount: float, 
                          payment_date: str = None, payment_mode: str = 'Check') -> dict:
        """Record a payment for an invoice"""
        invoice = self.get_invoice(invoice_id)
        
        payment_data = {
            'customer_id': invoice['customer_id'],
            'payment_mode': payment_mode,
            'amount': amount,
            'date': payment_date or datetime.now().strftime('%Y-%m-%d'),
            'invoices': [
                {
                    'invoice_id': invoice_id,
                    'amount_applied': amount
                }
            ]
        }
        
        result = self._api_request('POST', '/customerpayments', data=payment_data)
        return result.get('payment', {})
    
    # ============================================
    # Sync with Harbor
    # ============================================
    
    def sync_clients_to_zoho(self) -> dict:
        """
        Sync Harbor clients to Zoho Books as customers
        Creates customers for clients that don't exist in Zoho
        Updates zoho_customer_id in the database
        
        Returns: {created: int, linked: int, skipped: int}
        """
        logger.info("Syncing clients to Zoho Books...")
        
        # Get Harbor clients
        clients = db.get_all_clients()
        
        # Get existing Zoho customers
        zoho_customers = {c['contact_name'].lower(): c for c in self.get_customers()}
        
        stats = {'created': 0, 'linked': 0, 'skipped': 0}
        
        for client in clients:
            # Skip if already linked
            if client.get('zoho_customer_id'):
                stats['skipped'] += 1
                continue
            
            # Check if customer exists in Zoho
            existing = zoho_customers.get(client['name'].lower())
            
            if existing:
                # Link existing customer
                db.execute_db(
                    'UPDATE clients SET zoho_customer_id = ? WHERE id = ?',
                    [existing['contact_id'], client['id']]
                )
                stats['linked'] += 1
                logger.info(f"Linked client '{client['name']}' to existing Zoho customer")
            else:
                # Create new customer
                try:
                    new_customer = self.create_customer(
                        name=client['name'],
                        email=client.get('primary_contact_email'),
                        phone=client.get('primary_contact_phone')
                    )
                    
                    db.execute_db(
                        'UPDATE clients SET zoho_customer_id = ? WHERE id = ?',
                        [new_customer['contact_id'], client['id']]
                    )
                    stats['created'] += 1
                    logger.info(f"Created Zoho customer for '{client['name']}'")
                except Exception as e:
                    logger.error(f"Failed to create customer '{client['name']}': {e}")
        
        logger.info(f"Sync complete: {stats}")
        return stats
    
    def sync_invoices_from_zoho(self) -> int:
        """
        Sync invoices from Zoho Books to Harbor database
        
        Returns: Number of invoices synced
        """
        logger.info("Syncing invoices from Zoho Books...")
        
        # Get clients with Zoho IDs
        clients = db.get_all_clients()
        client_map = {c.get('zoho_customer_id'): c for c in clients if c.get('zoho_customer_id')}
        
        synced = 0
        
        for zoho_id, client in client_map.items():
            try:
                invoices = self.get_invoices(customer_id=zoho_id)
                
                for inv in invoices:
                    # Check if invoice exists in database
                    existing = db.query_db(
                        'SELECT id FROM invoices WHERE zoho_invoice_id = ?',
                        [inv['invoice_id']], one=True
                    )
                    
                    if existing:
                        # Update existing
                        db.execute_db('''
                            UPDATE invoices SET
                                status = ?, amount = ?, due_date = ?, synced_at = CURRENT_TIMESTAMP
                            WHERE zoho_invoice_id = ?
                        ''', [inv['status'], float(inv['total']), inv.get('due_date'), inv['invoice_id']])
                    else:
                        # Insert new
                        db.execute_db('''
                            INSERT INTO invoices 
                            (client_id, zoho_invoice_id, invoice_number, amount, status, invoice_date, due_date, synced_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', [
                            client['id'],
                            inv['invoice_id'],
                            inv.get('invoice_number'),
                            float(inv['total']),
                            inv['status'],
                            inv.get('date'),
                            inv.get('due_date')
                        ])
                        synced += 1
            
            except Exception as e:
                logger.error(f"Failed to sync invoices for {client['name']}: {e}")
        
        logger.info(f"Invoice sync complete: {synced} new invoices")
        return synced
    
    def create_invoice_for_client(self, client_code: str, description: str, 
                                   amount: float, due_date: str = None) -> dict:
        """
        Create an invoice for a client
        
        Args:
            client_code: Client login code
            description: Invoice line item description
            amount: Invoice amount
            due_date: Optional due date (YYYY-MM-DD)
        
        Returns:
            Created invoice
        """
        client = db.get_client_by_code(client_code)
        if not client:
            raise ValueError(f"Client not found: {client_code}")
        
        if not client.get('zoho_customer_id'):
            # Try to create/link customer first
            self.sync_clients_to_zoho()
            client = db.get_client_by_code(client_code)
            
            if not client.get('zoho_customer_id'):
                raise ValueError(f"Client not linked to Zoho: {client_code}")
        
        invoice = self.create_invoice(
            customer_id=client['zoho_customer_id'],
            line_items=[{'description': description, 'rate': amount, 'quantity': 1}],
            due_date=due_date
        )
        
        # Sync back to local database
        db.execute_db('''
            INSERT INTO invoices 
            (client_id, zoho_invoice_id, invoice_number, amount, status, invoice_date, due_date, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', [
            client['id'],
            invoice['invoice_id'],
            invoice.get('invoice_number'),
            float(invoice['total']),
            invoice['status'],
            invoice.get('date'),
            invoice.get('due_date')
        ])
        
        db.log_activity(
            action='invoice_created',
            description=f"Created invoice #{invoice.get('invoice_number')} for ${amount}",
            client_id=client['id'],
            performed_by='zoho_integration'
        )
        
        return invoice


# Global instance
zoho = ZohoIntegration()


# ============================================
# CLI
# ============================================

if __name__ == '__main__':
    import sys
    
    def print_usage():
        print("""
Zoho Books Integration CLI

Commands:
    auth                    Start OAuth flow to get refresh token
    callback <code>         Exchange auth code for tokens
    test                    Test connection
    customers               List customers
    invoices [status]       List invoices (status: draft, sent, overdue, paid)
    create-invoice          Create invoice (interactive)
    sync-clients            Sync clients to Zoho
    sync-invoices           Sync invoices from Zoho
    
Examples:
    python integrations/zoho.py auth
    python integrations/zoho.py test
    python integrations/zoho.py invoices unpaid
    python integrations/zoho.py sync-clients
""")
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'auth':
        if not config.ZOHO_CLIENT_ID:
            print("ZOHO_CLIENT_ID not configured in .env")
            sys.exit(1)
        
        auth_url = zoho.get_auth_url()
        print("\n1. Opening browser for Zoho authorization...")
        print(f"\n   If browser doesn't open, visit:\n   {auth_url}\n")
        webbrowser.open(auth_url)
        print("2. After authorizing, you'll be redirected to a localhost URL")
        print("3. Copy the 'code' parameter from the URL")
        code = input("\n4. Paste the code here: ").strip()
        
        if code:
            try:
                tokens = zoho.exchange_code_for_token(code)
                print("\n✓ Authorization successful!")
                print(f"\nAdd this to your .env file:")
                print(f"ZOHO_REFRESH_TOKEN={tokens.get('refresh_token')}")
            except Exception as e:
                print(f"\n✗ Error: {e}")
    
    elif cmd == 'callback' and len(sys.argv) > 2:
        code = sys.argv[2]
        try:
            tokens = zoho.exchange_code_for_token(code)
            print("\n✓ Authorization successful!")
            print(f"\nAdd this to your .env file:")
            print(f"ZOHO_REFRESH_TOKEN={tokens.get('refresh_token')}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    elif cmd == 'test':
        success, msg = zoho.test_connection()
        print(f"{'✓' if success else '✗'} {msg}")
    
    elif cmd == 'customers':
        if not zoho.is_configured():
            print("Zoho not configured. Add credentials to .env")
        else:
            customers = zoho.get_customers()
            print(f"\nZoho Customers ({len(customers)}):")
            for c in customers:
                print(f"  {c['contact_name']} - {c.get('email', 'No email')}")
    
    elif cmd == 'invoices':
        status = sys.argv[2] if len(sys.argv) > 2 else None
        if not zoho.is_configured():
            print("Zoho not configured. Add credentials to .env")
        else:
            invoices = zoho.get_invoices(status=status)
            print(f"\nInvoices ({len(invoices)}):")
            for inv in invoices:
                print(f"  #{inv.get('invoice_number')} - {inv['customer_name']} - ${inv['total']} ({inv['status']})")
    
    elif cmd == 'sync-clients':
        if not zoho.is_configured():
            print("Zoho not configured. Add credentials to .env")
        else:
            stats = zoho.sync_clients_to_zoho()
            print(f"\nSync complete:")
            print(f"  Created: {stats['created']}")
            print(f"  Linked: {stats['linked']}")
            print(f"  Skipped: {stats['skipped']}")
    
    elif cmd == 'sync-invoices':
        if not zoho.is_configured():
            print("Zoho not configured. Add credentials to .env")
        else:
            count = zoho.sync_invoices_from_zoho()
            print(f"\nSynced {count} new invoice(s)")
    
    elif cmd == 'create-invoice':
        if not zoho.is_configured():
            print("Zoho not configured. Add credentials to .env")
        else:
            print("\nCreate Invoice")
            client_code = input("Client code: ")
            description = input("Description: ")
            amount = float(input("Amount: $"))
            due_date = input("Due date (YYYY-MM-DD, or Enter for 30 days): ").strip()
            
            if not due_date:
                due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            try:
                invoice = zoho.create_invoice_for_client(client_code, description, amount, due_date)
                print(f"\n✓ Invoice created!")
                print(f"  Number: {invoice.get('invoice_number')}")
                print(f"  Amount: ${invoice.get('total')}")
            except Exception as e:
                print(f"\n✗ Error: {e}")
    
    else:
        print(f"Unknown command: {cmd}")
        print_usage()
