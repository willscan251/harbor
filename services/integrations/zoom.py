"""
Harbor - Zoom Integration
Handles meeting scheduling, recordings, and transcript import

SETUP:
1. Go to https://marketplace.zoom.us/
2. Develop → Build App → Server-to-Server OAuth
3. Name: "Harbor"
4. Add scopes: meeting:write:admin, meeting:read:admin, recording:read:admin, user:read:admin
5. Activate app and copy credentials to .env
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, List

import requests

import config
import database as db

logger = logging.getLogger('integration.zoom')

class ZoomIntegration:
    """Zoom API integration for Harbor"""
    
    def __init__(self):
        self.access_token = None
        self.token_expires_at = None
        self.base_url = 'https://api.zoom.us/v2'
    
    def is_configured(self) -> bool:
        """Check if Zoom credentials are configured"""
        return config.is_configured('zoom')
    
    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if needed"""
        if not self.is_configured():
            raise RuntimeError("Zoom credentials not configured")
        
        # Check if current token is valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return self.access_token
        
        # Get new token
        credentials = f"{config.ZOOM_CLIENT_ID}:{config.ZOOM_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        response = requests.post(
            'https://zoom.us/oauth/token',
            headers={
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'grant_type': 'account_credentials',
                'account_id': config.ZOOM_ACCOUNT_ID
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.token_expires_at = datetime.now() + timedelta(seconds=data['expires_in'])
            logger.info("Zoom access token refreshed")
            return self.access_token
        else:
            logger.error(f"Zoom auth failed: {response.status_code} - {response.text}")
            raise RuntimeError(f"Zoom authentication failed: {response.text}")
    
    def _api_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make an authenticated API request to Zoom"""
        token = self._get_access_token()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params or data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code in [200, 201, 204]:
            return response.json() if response.text else {'success': True}
        else:
            logger.error(f"Zoom API error: {response.status_code} - {response.text}")
            raise RuntimeError(f"Zoom API error: {response.status_code}")
    
    def test_connection(self) -> tuple:
        """Test the Zoom connection. Returns (success, message)"""
        if not self.is_configured():
            return False, "Zoom credentials not configured in .env"
        
        try:
            users = self.get_users()
            return True, f"Connected! Found {len(users)} user(s): {', '.join(u['email'] for u in users)}"
        except Exception as e:
            return False, str(e)
    
    # ============================================
    # Users
    # ============================================
    
    def get_users(self) -> List[dict]:
        """Get all Zoom users in the account"""
        result = self._api_request('GET', '/users', params={'page_size': 100})
        return result.get('users', [])
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Find a Zoom user by email"""
        users = self.get_users()
        return next((u for u in users if u['email'].lower() == email.lower()), None)
    
    # ============================================
    # Meetings
    # ============================================
    
    def schedule_meeting(self, host_email: str, topic: str, start_time: datetime,
                         duration_minutes: int = 60, agenda: str = None,
                         client_id: int = None) -> dict:
        """
        Schedule a new Zoom meeting
        
        Args:
            host_email: Email of the Zoom user who will host
            topic: Meeting title
            start_time: When the meeting starts
            duration_minutes: Meeting duration
            agenda: Optional agenda text
            client_id: Optional client ID to link in database
        
        Returns:
            Meeting details including join_url
        """
        user = self.get_user_by_email(host_email)
        if not user:
            raise ValueError(f"Zoom user not found: {host_email}")
        
        meeting_data = {
            'topic': topic,
            'type': 2,  # Scheduled meeting
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'duration': duration_minutes,
            'timezone': config.TIMEZONE,
            'settings': {
                'host_video': True,
                'participant_video': True,
                'join_before_host': True,
                'mute_upon_entry': False,
                'auto_recording': 'cloud',  # Enable for transcript capture
                'waiting_room': False
            }
        }
        
        if agenda:
            meeting_data['agenda'] = agenda
        
        result = self._api_request('POST', f"/users/{user['id']}/meetings", data=meeting_data)
        
        # Save to database if client specified
        if client_id and result:
            db.execute_db('''
                INSERT INTO meetings (client_id, title, meeting_date, zoom_meeting_id, zoom_recording_url, transcript_source)
                VALUES (?, ?, ?, ?, ?, 'zoom')
            ''', [client_id, topic, start_time.isoformat(), str(result.get('id')), result.get('join_url')])
            
            db.log_activity(
                action='meeting_scheduled',
                description=f"Scheduled Zoom meeting: {topic}",
                client_id=client_id,
                performed_by='zoom_integration'
            )
        
        logger.info(f"Scheduled meeting: {topic} at {start_time}")
        return result
    
    def schedule_client_meeting(self, client_code: str, host_email: str,
                                 start_time: datetime, duration_minutes: int = 60,
                                 custom_topic: str = None) -> dict:
        """
        Schedule a meeting with a client
        
        Args:
            client_code: Client login code (e.g., 'acf7428')
            host_email: Email of staff member hosting
            start_time: Meeting start time
            duration_minutes: Duration
            custom_topic: Optional custom topic
        
        Returns:
            Meeting details
        """
        client = db.get_client_by_code(client_code)
        if not client:
            raise ValueError(f"Client not found: {client_code}")
        
        topic = custom_topic or f"Meeting with {client['name']}"
        
        return self.schedule_meeting(
            host_email=host_email,
            topic=topic,
            start_time=start_time,
            duration_minutes=duration_minutes,
            client_id=client['id']
        )
    
    def get_upcoming_meetings(self, host_email: str = None) -> List[dict]:
        """Get upcoming scheduled meetings"""
        meetings = []
        
        users = [self.get_user_by_email(host_email)] if host_email else self.get_users()
        users = [u for u in users if u]  # Filter None
        
        for user in users:
            try:
                result = self._api_request('GET', f"/users/{user['id']}/meetings", 
                                          params={'type': 'upcoming', 'page_size': 50})
                for m in result.get('meetings', []):
                    m['host_email'] = user['email']
                    meetings.append(m)
            except Exception as e:
                logger.warning(f"Failed to get meetings for {user['email']}: {e}")
        
        # Sort by start time
        meetings.sort(key=lambda m: m.get('start_time', ''))
        return meetings
    
    def get_meeting(self, meeting_id: str) -> dict:
        """Get details for a specific meeting"""
        return self._api_request('GET', f'/meetings/{meeting_id}')
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Cancel/delete a meeting"""
        try:
            self._api_request('DELETE', f'/meetings/{meeting_id}')
            return True
        except:
            return False
    
    # ============================================
    # Recordings & Transcripts
    # ============================================
    
    def get_recordings(self, days: int = 7, host_email: str = None) -> List[dict]:
        """Get cloud recordings from the past N days"""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        recordings = []
        users = [self.get_user_by_email(host_email)] if host_email else self.get_users()
        users = [u for u in users if u]
        
        for user in users:
            try:
                result = self._api_request('GET', f"/users/{user['id']}/recordings",
                                          params={'from': from_date, 'to': to_date})
                for r in result.get('meetings', []):
                    r['host_email'] = user['email']
                    recordings.append(r)
            except Exception as e:
                logger.warning(f"Failed to get recordings for {user['email']}: {e}")
        
        return recordings
    
    def get_recording_files(self, meeting_id: str) -> dict:
        """Get recording files for a specific meeting"""
        return self._api_request('GET', f'/meetings/{meeting_id}/recordings')
    
    def download_transcript(self, download_url: str) -> Optional[str]:
        """Download a transcript file from Zoom"""
        token = self._get_access_token()
        
        try:
            response = requests.get(
                download_url,
                headers={'Authorization': f'Bearer {token}'},
                allow_redirects=True
            )
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to download transcript: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Transcript download error: {e}")
            return None
    
    def sync_transcripts(self, days: int = 7) -> int:
        """
        Sync transcripts from recent Zoom recordings into the database
        
        Returns number of transcripts imported
        """
        logger.info(f"Syncing Zoom transcripts from last {days} days...")
        
        recordings = self.get_recordings(days=days)
        imported = 0
        
        for recording in recordings:
            meeting_uuid = recording.get('uuid')
            topic = recording.get('topic', 'Untitled')
            
            try:
                # Get recording details
                details = self.get_recording_files(meeting_uuid)
                
                # Find transcript file
                transcript_file = None
                for file in details.get('recording_files', []):
                    if file.get('file_type') == 'TRANSCRIPT':
                        transcript_file = file
                        break
                
                if not transcript_file:
                    continue
                
                # Download transcript
                download_url = transcript_file.get('download_url')
                transcript_text = self.download_transcript(download_url)
                
                if not transcript_text:
                    continue
                
                # Find matching meeting in database
                meeting = db.dict_from_row(db.query_db('''
                    SELECT id, client_id FROM meetings 
                    WHERE zoom_meeting_id = ? AND transcript IS NULL
                ''', [str(recording.get('id'))], one=True))
                
                if meeting:
                    # Update existing meeting
                    db.execute_db('''
                        UPDATE meetings SET transcript = ? WHERE id = ?
                    ''', [transcript_text, meeting['id']])
                    
                    db.log_activity(
                        action='transcript_imported',
                        description=f"Imported Zoom transcript for: {topic}",
                        client_id=meeting['client_id'],
                        entity_type='meeting',
                        entity_id=meeting['id'],
                        performed_by='zoom_integration'
                    )
                    
                    imported += 1
                    logger.info(f"Imported transcript: {topic}")
                else:
                    # Could optionally create new meeting record here
                    logger.debug(f"No matching meeting found for: {topic}")
            
            except Exception as e:
                logger.error(f"Failed to process recording {topic}: {e}")
        
        logger.info(f"Transcript sync complete. Imported {imported} transcript(s).")
        return imported


# Global instance
zoom = ZoomIntegration()


# ============================================
# CLI
# ============================================

if __name__ == '__main__':
    import sys
    
    def print_usage():
        print("""
Zoom Integration CLI

Commands:
    test                    Test connection
    users                   List Zoom users
    meetings                Show upcoming meetings
    schedule                Schedule a new meeting (interactive)
    recordings [days]       Show recent recordings
    sync [days]             Sync transcripts from recordings
    
Examples:
    python integrations/zoom.py test
    python integrations/zoom.py meetings
    python integrations/zoom.py sync 14
""")
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'test':
        success, msg = zoom.test_connection()
        print(f"{'✓' if success else '✗'} {msg}")
    
    elif cmd == 'users':
        if not zoom.is_configured():
            print("Zoom not configured. Add credentials to .env")
        else:
            users = zoom.get_users()
            print(f"\nZoom Users ({len(users)}):")
            for u in users:
                print(f"  {u['email']} - {u['first_name']} {u['last_name']}")
    
    elif cmd == 'meetings':
        if not zoom.is_configured():
            print("Zoom not configured. Add credentials to .env")
        else:
            meetings = zoom.get_upcoming_meetings()
            print(f"\nUpcoming Meetings ({len(meetings)}):")
            for m in meetings:
                print(f"  {m.get('start_time', 'TBD')} - {m['topic']}")
                print(f"    Host: {m.get('host_email')}")
                print(f"    Join: {m.get('join_url')}")
                print()
    
    elif cmd == 'recordings':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        if not zoom.is_configured():
            print("Zoom not configured. Add credentials to .env")
        else:
            recordings = zoom.get_recordings(days=days)
            print(f"\nRecordings (last {days} days): {len(recordings)}")
            for r in recordings:
                print(f"  {r.get('start_time')} - {r.get('topic')}")
                print(f"    Duration: {r.get('duration', 0)} minutes")
    
    elif cmd == 'sync':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        if not zoom.is_configured():
            print("Zoom not configured. Add credentials to .env")
        else:
            count = zoom.sync_transcripts(days=days)
            print(f"Synced {count} transcript(s)")
    
    elif cmd == 'schedule':
        if not zoom.is_configured():
            print("Zoom not configured. Add credentials to .env")
        else:
            print("\nSchedule a Meeting")
            host = input("Host email: ")
            client = input("Client code (or press Enter to skip): ").strip() or None
            topic = input("Topic: ")
            date_str = input("Date/time (YYYY-MM-DD HH:MM): ")
            
            try:
                start = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                if client:
                    result = zoom.schedule_client_meeting(client, host, start, custom_topic=topic)
                else:
                    result = zoom.schedule_meeting(host, topic, start)
                
                print(f"\n✓ Meeting scheduled!")
                print(f"  Join URL: {result.get('join_url')}")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    else:
        print(f"Unknown command: {cmd}")
        print_usage()
