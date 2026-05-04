import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# [CONSTRAINTS] OAuth scopes - only what we need
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']

# [CONTEXT] Calendar service singleton
class CalendarService:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth2 flow - user must have credentials.json from Google Cloud Console"""
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(self.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            if creds:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
        
        if creds:
            self.service = build('calendar', 'v3', credentials=creds)
    
    def is_authenticated(self) -> bool:
        return self.service is not None
    
    def list_events(self, days_ahead: int = 7, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch upcoming calendar events"""
        if not self.service:
            return [{"error": "Not authenticated. Please set up Google Calendar credentials."}]
        
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def create_event(self, summary: str, start_time: str, end_time: str, 
                     description: str = "", location: str = "") -> Dict[str, Any]:
        """Create a calendar event
        
        Args:
            summary: Event title
            start_time: ISO format datetime (e.g., 2024-01-15T10:00:00)
            end_time: ISO format datetime
            description: Optional description
            location: Optional location
        """
        if not self.service:
            return {"error": "Not authenticated"}
        
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        
        return self.service.events().insert(calendarId='primary', body=event).execute()
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event by ID"""
        if not self.service:
            return False
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception:
            return False
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get a single event"""
        if not self.service:
            return None
        try:
            return self.service.events().get(calendarId='primary', eventId=event_id).execute()
        except Exception:
            return None

# Global calendar instance
_calendar = None

def get_calendar_service() -> CalendarService:
    global _calendar
    if _calendar is None:
        _calendar = CalendarService()
    return _calendar

# [GOAL] Calendar tool functions for agent
def list_calendar_events(days_ahead: int = 7) -> str:
    """List upcoming calendar events.
    
    Args:
        days_ahead: Number of days to look ahead (default 7)
    
    Returns:
        Formatted list of events
    """
    cal = get_calendar_service()
    events = cal.list_events(days_ahead)
    
    if not events or (len(events) == 1 and 'error' in events[0]):
        return "No events found or calendar not configured."
    
    output = f"=== UPCOMING EVENTS ({days_ahead} days) ===\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        output += f"\n📅 {start}\n"
        output += f"   {event.get('summary', 'No title')}\n"
        if event.get('location'):
            output += f"   📍 {event['location']}\n"
        if event.get('description'):
            output += f"   📝 {event['description'][:100]}\n"
        output += f"   ID: {event['id']}\n"
    return output

def create_calendar_event(title: str, start: str, end: str, 
                         description: str = "", location: str = "") -> str:
    """Create a new calendar event.
    
    Args:
        title: Event title
        start: Start time in ISO format (e.g., 2024-01-15T10:00:00)
        end: End time in ISO format
        description: Optional description
        location: Optional location
    
    Returns:
        Confirmation with event ID or error
    """
    cal = get_calendar_service()
    result = cal.create_event(title, start, end, description, location)
    
    if 'error' in result:
        return f"Error: {result['error']}"
    return f"Created event '{title}' with ID: {result['id']}"

def delete_calendar_event(event_id: str) -> str:
    """Delete a calendar event by ID.
    
    Args:
        event_id: The calendar event ID (from list_calendar_events)
    
    Returns:
        Deletion confirmation
    """
    cal = get_calendar_service()
    success = cal.delete_event(event_id)
    return f"Event {event_id} deleted." if success else f"Failed to delete event {event_id}"

def get_calendar_event(event_id: str) -> str:
    """Get details of a specific event.
    
    Args:
        event_id: The calendar event ID
    
    Returns:
        Event details
    """
    cal = get_calendar_service()
    event = cal.get_event(event_id)
    
    if not event:
        return f"Event {event_id} not found."
    
    output = f"=== EVENT DETAILS ===\n"
    output += f"Title: {event.get('summary', 'No title')}\n"
    output += f"Start: {event['start'].get('dateTime', event['start'].get('date'))}\n"
    output += f"End: {event['end'].get('dateTime', event['end'].get('date'))}\n"
    if event.get('location'):
        output += f"Location: {event['location']}\n"
    if event.get('description'):
        output += f"Description: {event['description']}\n"
    output += f"ID: {event['id']}\n"
    return output