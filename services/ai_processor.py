"""
Harbor - AI Processor
Processes meeting transcripts and generates action items using Claude
"""

import json
import base64
import config
import database as db

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠ anthropic not installed. Run: pip install anthropic")

def get_client():
    """Get Anthropic client"""
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("Anthropic package not installed")
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    return Anthropic(api_key=config.ANTHROPIC_API_KEY)

def process_meeting_transcript(transcript: str, client_name: str = None, 
                               meeting_context: str = None) -> dict:
    """
    Process a meeting transcript and extract:
    - Summary
    - Action items with assignees and due dates
    - Key decisions
    - Follow-up items
    
    Returns dict with: summary, action_items, decisions, follow_ups
    """
    
    client = get_client()
    
    context = f"Client: {client_name}\n" if client_name else ""
    if meeting_context:
        context += f"Context: {meeting_context}\n"
    
    prompt = f"""Analyze this meeting transcript and extract structured information.

{context}
TRANSCRIPT:
{transcript}

Please provide:
1. A concise summary (2-3 paragraphs)
2. Action items with:
   - Task description
   - Who it's assigned to (if mentioned)
   - Due date (if mentioned)
   - Priority (high/medium/low based on context)
3. Key decisions made
4. Items needing follow-up

Respond in this exact JSON format:
{{
    "summary": "Meeting summary here...",
    "action_items": [
        {{
            "task": "Description of task",
            "assigned_to": "Person name or null",
            "due_date": "YYYY-MM-DD or null",
            "priority": "high|medium|low"
        }}
    ],
    "decisions": [
        "Decision 1",
        "Decision 2"
    ],
    "follow_ups": [
        "Follow-up item 1",
        "Follow-up item 2"
    ]
}}

Return ONLY valid JSON, no other text."""

    response = client.messages.create(
        model=config.AI_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    
    # Clean up JSON if wrapped in markdown
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    
    return json.loads(text)

def process_and_save_meeting(meeting_id: int) -> dict:
    """
    Process a meeting's transcript and save results to database
    """
    # Get meeting
    meeting = db.dict_from_row(db.query_db(
        'SELECT * FROM meetings WHERE id = ?', [meeting_id], one=True
    ))
    
    if not meeting:
        raise ValueError(f"Meeting not found: {meeting_id}")
    
    if not meeting['transcript']:
        raise ValueError(f"Meeting has no transcript: {meeting_id}")
    
    # Get client name
    client = db.get_client_by_id(meeting['client_id'])
    client_name = client['name'] if client else None
    
    # Process transcript
    result = process_meeting_transcript(
        transcript=meeting['transcript'],
        client_name=client_name
    )
    
    # Save summary to meeting
    conn = db.get_db()
    conn.execute('''
        UPDATE meetings 
        SET ai_summary = ?, ai_action_items = ?, processed = 1
        WHERE id = ?
    ''', [result['summary'], json.dumps(result['action_items']), meeting_id])
    conn.commit()
    
    # Create tasks from action items
    for item in result['action_items']:
        conn.execute('''
            INSERT INTO tasks (client_id, meeting_id, title, description, assigned_to, due_date, priority, status, client_visible)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 1)
        ''', [
            meeting['client_id'],
            meeting_id,
            item['task'][:200],  # Truncate if too long
            item['task'],
            item.get('assigned_to'),
            item.get('due_date'),
            item.get('priority', 'medium')
        ])
    
    conn.commit()
    conn.close()
    
    # Log activity
    db.log_activity(
        action='meeting_processed',
        description=f"Processed meeting transcript, created {len(result['action_items'])} tasks",
        client_id=meeting['client_id'],
        entity_type='meeting',
        entity_id=meeting_id,
        performed_by='ai_processor'
    )
    
    return result

def generate_agenda(client_id: int, include_pending_tasks: bool = True,
                    include_recent_notes: bool = True) -> str:
    """
    Generate a meeting agenda for a client based on:
    - Pending tasks
    - Recent meeting notes
    - Follow-up items
    """
    
    client = db.get_client_by_id(client_id)
    if not client:
        raise ValueError(f"Client not found: {client_id}")
    
    # Get pending tasks
    tasks = []
    if include_pending_tasks:
        tasks = db.rows_to_dicts(db.query_db('''
            SELECT title, due_date, priority FROM tasks 
            WHERE client_id = ? AND status = 'pending'
            ORDER BY 
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                due_date
            LIMIT 10
        ''', [client_id]))
    
    # Get recent meeting summaries
    recent_meetings = []
    if include_recent_notes:
        recent_meetings = db.rows_to_dicts(db.query_db('''
            SELECT title, meeting_date, ai_summary FROM meetings
            WHERE client_id = ? AND ai_summary IS NOT NULL
            ORDER BY meeting_date DESC
            LIMIT 3
        ''', [client_id]))
    
    # Build context for AI
    context = f"Client: {client['name']}\n\n"
    
    if tasks:
        context += "PENDING TASKS:\n"
        for t in tasks:
            context += f"- [{t['priority']}] {t['title']}"
            if t['due_date']:
                context += f" (due: {t['due_date']})"
            context += "\n"
        context += "\n"
    
    if recent_meetings:
        context += "RECENT MEETINGS:\n"
        for m in recent_meetings:
            context += f"- {m['meeting_date']}: {m['title']}\n"
            if m['ai_summary']:
                context += f"  Summary: {m['ai_summary'][:200]}...\n"
        context += "\n"
    
    # Generate agenda
    api_client = get_client()
    
    prompt = f"""Generate a meeting agenda for an upcoming consulting meeting.

{context}

Create a professional agenda with:
1. Welcome and check-in (5 min)
2. Review of action items from last meeting
3. Main discussion topics (based on pending tasks and recent context)
4. New business
5. Next steps and action items
6. Schedule next meeting

Format as a clean, professional agenda that could be shared with the client.
Include suggested time allocations for each section.
Total meeting time: 60 minutes."""

    response = api_client.messages.create(
        model=config.AI_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    agenda_content = response.content[0].text.strip()
    
    # Save agenda to database
    agenda_id = db.execute_db('''
        INSERT INTO agendas (client_id, title, agenda_date, content, ai_generated)
        VALUES (?, ?, DATE('now'), ?, 1)
    ''', [client_id, f"Meeting Agenda - {client['name']}", agenda_content])
    
    db.log_activity(
        action='agenda_generated',
        description=f"Generated meeting agenda",
        client_id=client_id,
        entity_type='agenda',
        entity_id=agenda_id,
        performed_by='ai_processor'
    )
    
    return agenda_content

def generate_status_report(client_id: int, period_days: int = 30) -> str:
    """
    Generate a status report for a client covering recent activity
    """
    
    client = db.get_client_by_id(client_id)
    if not client:
        raise ValueError(f"Client not found: {client_id}")
    
    # Get completed tasks
    completed_tasks = db.rows_to_dicts(db.query_db('''
        SELECT title, completed_at FROM tasks
        WHERE client_id = ? AND status = 'completed'
        AND completed_at >= DATE('now', ?)
        ORDER BY completed_at DESC
    ''', [client_id, f'-{period_days} days']))
    
    # Get pending tasks
    pending_tasks = db.rows_to_dicts(db.query_db('''
        SELECT title, due_date, priority FROM tasks
        WHERE client_id = ? AND status = 'pending'
        ORDER BY due_date
    ''', [client_id]))
    
    # Get meetings
    meetings = db.rows_to_dicts(db.query_db('''
        SELECT title, meeting_date, ai_summary FROM meetings
        WHERE client_id = ? AND meeting_date >= DATE('now', ?)
        ORDER BY meeting_date DESC
    ''', [client_id, f'-{period_days} days']))
    
    # Build context
    context = f"Client: {client['name']}\nPeriod: Last {period_days} days\n\n"
    
    context += f"COMPLETED TASKS ({len(completed_tasks)}):\n"
    for t in completed_tasks[:10]:
        context += f"- {t['title']}\n"
    
    context += f"\nPENDING TASKS ({len(pending_tasks)}):\n"
    for t in pending_tasks[:10]:
        context += f"- {t['title']}"
        if t['due_date']:
            context += f" (due: {t['due_date']})"
        context += "\n"
    
    context += f"\nMEETINGS ({len(meetings)}):\n"
    for m in meetings[:5]:
        context += f"- {m['meeting_date']}: {m['title']}\n"
    
    # Generate report
    api_client = get_client()
    
    prompt = f"""Generate a professional status report for a nonprofit consulting engagement.

{context}

Create a report with:
1. Executive Summary (2-3 sentences)
2. Accomplishments This Period
3. In Progress / Pending Items
4. Upcoming Priorities
5. Any Concerns or Blockers

Keep it concise and professional. This will be shared with the client."""

    response = api_client.messages.create(
        model=config.AI_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()

def categorize_file(filename: str, content_preview: str = None) -> dict:
    """
    Use AI to determine where a file should be stored in the SharePoint structure.
    
    Two-pass approach:
    1. First pass: categorize using client list + aliases
    2. If unknown: second pass with web search to identify the organization
    
    Returns: {
        client_id: int or None,
        client_code: str or None,
        destination: str,        # Full path like "The Scanland Group/Clients/Baldwin ARC/Proposals"
        category: str,           # Subfolder name
        confidence: str,         # high/medium/low
        reason: str
    }
    """
    
    clients = db.get_all_clients()
    clients_text = "\n".join([
        f"- ID:{c['id']} | Name:{c['name']} | Short:{c.get('short_name', 'N/A')}"
        for c in clients
    ]) if clients else "(No clients in database)"
    
    # Load client aliases
    aliases = db.get_all_aliases()
    aliases_text = ""
    if aliases:
        aliases_text = "\n=== CLIENT ALIASES & PROGRAMS ===\n"
        aliases_text += "These names/programs are KNOWN to belong to specific clients:\n"
        for a in aliases:
            aliases_text += f"  - \"{a['alias']}\" → belongs to {a['client_name']} (ID:{a['client_id']}, type: {a['alias_type']})\n"
    
    # Build content section
    content_section = ""
    if content_preview:
        preview_text = content_preview[:3000]
        content_section = f"""
DOCUMENT CONTENT (extracted from the file - READ THIS CAREFULLY):
---
{preview_text}
---
"""
    
    prompt = _build_categorize_prompt(filename, content_section, clients_text, aliases_text)

    api_client = get_client()
    
    response = api_client.messages.create(
        model=config.AI_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = _parse_categorize_response(response.content[0].text, clients)
    
    # If low confidence or _unsorted, try web search fallback
    if result.get('confidence') == 'low' or result.get('destination') == '_unsorted':
        web_result = _web_search_fallback(filename, content_preview, clients, clients_text, aliases_text)
        if web_result and web_result.get('confidence') in ['high', 'medium']:
            return web_result
    
    return result


def _build_categorize_prompt(filename: str, content_section: str, clients_text: str, aliases_text: str) -> str:
    """Build the categorization prompt with the full folder hierarchy."""
    
    return f"""You are a document filing assistant for Scanland & Co and its subsidiary The Scanland Group (TSG), a nonprofit consulting firm. Your job is to determine EXACTLY where this file should be stored.

FILENAME: {filename}
{content_section}
=== ACTIVE CLIENTS (under The Scanland Group) ===
{clients_text}
{aliases_text}
=== SHAREPOINT FOLDER STRUCTURE ===
The drive is organized as follows:

Scanland & Co/                        ← Parent company (Scanland & Co)
  - Finance                           (Scanland & Co company taxes, payroll, budgets)
  - Legal                             (Scanland & Co contracts, insurance, compliance)
  - Admin                             (Scanland & Co admin, internal memos)
  - Operations                        (Scanland & Co operational docs)

The Scanland Group/                   ← TSG subsidiary
  Clients/[Client Name]/
    - Meeting Notes                   (meeting notes, agendas, minutes, transcripts)
    - Contracts                       (signed agreements, signed MOUs, executed contracts)
    - Proposals                       (proposals, scope of work, engagement letters, program descriptions)
    - Reports                         (completed deliverables, assessments, evaluations, strategic plans)
    - Financials                      (client IRS letters, client 990s, client invoices, budgets, audits, tax docs)
    - Correspondence                  (emails, letters, memos about/with client)
    - _NeedsFolder                    (client docs that don't fit categories above)
  Company/
    - Finance                         (TSG company taxes, TSG IRS docs, TSG invoices, TSG payroll — ONLY for TSG itself)
    - Legal                           (TSG contracts, independent contractor agreements, insurance)
    - HR                              (employee docs, cover letters, resumes, job applications)
    - Admin                           (general TSG admin, internal memos)
  Marketing/
    - Brand Assets, Website, Social Media, Proposals
  Resources/
    - Templates, Training, Reference
  Archive/

Harbor Inbox/                         ← Intake folder (files go here first)

=== INSTRUCTIONS ===

STEP 1 - READ THE DOCUMENT CONTENT:
You MUST read the extracted document content carefully. Content is the authority, not the filename.

STEP 2 - DETERMINE WHO THIS IS FOR:
TSG is a nonprofit consulting firm. Their clients are nonprofit organizations.
Documents like IRS letters, 990s, tax docs, financial statements could belong to ANY client OR to TSG.
READ THE CONTENT to figure out who the document is addressed to/about.

If a program name or organization appears in the content:
  - First check the ALIASES list above — it may already be mapped to a client
  - Then check the client list for partial name matches
  - If still no match, this may be a new/unknown client

STEP 3 - ROUTING:
All TSG client paths start with: The Scanland Group/Clients/[Client Name]/[Category]
All TSG company paths start with: The Scanland Group/Company/[Category]
All TSG marketing: The Scanland Group/Marketing/[Category]
Parent company docs: Scanland & Co/[Category]

STEP 4 - EXAMPLES:
  - IRS letter for "Striving for Greatness" → The Scanland Group/Clients/Striving for Greatness/Financials
  - IRS letter for "The Scanland Group" → The Scanland Group/Company/Finance
  - Contractor agreement for TSG → The Scanland Group/Company/Legal
  - Cover letter from job applicant → The Scanland Group/Company/HR
  - Proposal to a client → The Scanland Group/Clients/[Client Name]/Proposals
  - Email about TSG website → The Scanland Group/Marketing/Website
  - Scanland & Co tax document → Scanland & Co/Finance

STEP 5 - WHEN UNSURE:
Pick the closest match. Only use "_unsorted" if you truly cannot determine anything.

Respond in this EXACT format:
CLIENT_ID: [number or "none"]
DESTINATION: [full path like "The Scanland Group/Clients/Baldwin ARC/Financials" or "Scanland & Co/Finance"]
CATEGORY: [subfolder name]
CONFIDENCE: [high/medium/low]
REASON: [what content led to this decision]"""


def _web_search_fallback(filename: str, content_preview: str, clients: list, 
                          clients_text: str, aliases_text: str) -> dict:
    """
    When initial categorization fails, use web search to try to identify
    unknown organizations and connect them to existing clients.
    """
    # Extract the unknown org name from content or filename
    search_context = content_preview[:1000] if content_preview else filename
    
    try:
        api_client = get_client()
        
        prompt = f"""A document was found that mentions an organization we can't match to our client list.

FILENAME: {filename}
CONTENT SNIPPET: {search_context[:500]}

OUR CLIENTS:
{clients_text}
{aliases_text}

Please search the web to determine if the organization mentioned in this document is related to, 
a program of, or associated with any of our existing clients listed above. 
Look for connections like: parent organizations, DBAs, programs, fiscal sponsors, affiliated churches, etc.

After searching, respond in this EXACT format:
CLIENT_ID: [number or "none"]
DESTINATION: [full SharePoint path]
CATEGORY: [subfolder name]
CONFIDENCE: [high/medium/low]
REASON: [what you found that connects this to a client, or why it doesn't match]"""

        response = api_client.messages.create(
            model=config.AI_MODEL,
            max_tokens=500,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text from response (may have multiple content blocks due to tool use)
        text_parts = [block.text for block in response.content if hasattr(block, 'text')]
        full_text = "\n".join(text_parts)
        
        if full_text.strip():
            return _parse_categorize_response(full_text, clients)
        
    except Exception as e:
        import logging
        logging.getLogger('ai_processor').warning(f"Web search fallback failed: {e}")
    
    return None


def _parse_categorize_response(text: str, clients: list) -> dict:
    """Parse the AI's categorization response into a structured result."""
    text = text.strip()
    
    result = {}
    for line in text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            clean_key = key.strip().lower().replace(' ', '_')
            if clean_key in ['client_id', 'destination', 'category', 'confidence', 'reason']:
                result[clean_key] = value.strip()
    
    # Resolve client info
    client_id_raw = result.get('client_id', 'none')
    client_id = None
    client_code = None
    
    if client_id_raw and client_id_raw.lower() not in ['none', 'unknown', 'n/a', '']:
        try:
            client_id = int(client_id_raw)
            if clients:
                client = next((c for c in clients if c['id'] == client_id), None)
                if client:
                    client_code = client['code']
        except (ValueError, TypeError):
            client_id = None
    
    return {
        'client_id': client_id,
        'client_code': client_code,
        'destination': result.get('destination', '_unsorted'),
        'category': result.get('category', '_unsorted'),
        'confidence': result.get('confidence', 'low'),
        'reason': result.get('reason', '')
    }


def categorize_image_file(filename: str, image_path: str) -> dict:
    """
    Use Claude's vision API to read and categorize an image file.
    Works with JPG, JPEG, PNG, GIF files.
    
    Returns same format as categorize_file.
    """
    
    # Read image and encode as base64
    ext = image_path.rsplit('.', 1)[-1].lower()
    media_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg', 
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    media_type = media_types.get(ext, 'image/jpeg')
    
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')
    
    clients = db.get_all_clients()
    clients_text = "\n".join([
        f"- ID:{c['id']} | Name:{c['name']} | Short:{c.get('short_name', 'N/A')}"
        for c in clients
    ]) if clients else "(No clients in database)"
    
    # Load client aliases
    aliases = db.get_all_aliases()
    aliases_text = ""
    if aliases:
        aliases_text = "\n=== CLIENT ALIASES & PROGRAMS ===\n"
        aliases_text += "These names are KNOWN to belong to specific clients:\n"
        for a in aliases:
            aliases_text += f"  - \"{a['alias']}\" → belongs to {a['client_name']} (ID:{a['client_id']})\n"
    
    prompt = f"""You are a document filing assistant for The Scanland Group (TSG), a nonprofit consulting firm.

Look at this image carefully. It is a scanned document, photo of a letter, or similar image file.
READ ALL THE TEXT in the image and determine where this file should be stored.

FILENAME: {filename}

=== ACTIVE CLIENTS ===
{clients_text}
{aliases_text}

=== SHAREPOINT FOLDER STRUCTURE ===
The Scanland Group/Clients/[Client Name]/
  - Meeting Notes, Contracts, Proposals, Reports, Financials, Correspondence, _NeedsFolder

The Scanland Group/Company/
  - Finance     (TSG company taxes, TSG IRS docs, TSG invoices, TSG payroll)
  - Legal       (TSG contracts, independent contractor agreements, insurance)
  - HR          (employee docs, cover letters, resumes, job applications)
  - Admin       (general TSG admin, internal memos)

The Scanland Group/Marketing/
  - Brand Assets, Website, Social Media, Proposals

Scanland & Co/
  - Finance, Legal, Admin, Operations  (parent company docs)

=== CRITICAL INSTRUCTIONS ===
1. READ THE TEXT IN THE IMAGE - look for names, addresses, organizations mentioned
2. CHECK ALIASES FIRST - if the organization name matches an alias above, route to THAT CLIENT
3. If it's an IRS letter/tax doc, look at WHO it's addressed to:
   - Addressed to an alias org (e.g. Trinity Family) → route to the mapped client (e.g. Community Connect CDC)
   - Addressed to a client org → The Scanland Group/Clients/[Client Name]/Financials
   - Addressed to The Scanland Group or TSG → The Scanland Group/Company/Finance
   - Addressed to Scanland & Co → Scanland & Co/Finance
4. Match any organization names to BOTH the client list AND the aliases list
5. ALL client paths must start with "The Scanland Group/Clients/"
6. If you cannot read the text clearly, say so in your reason

Respond in this EXACT format:
CLIENT_ID: [number or "none"]
DESTINATION: [full path like "The Scanland Group/Clients/Baldwin ARC/Financials" or "The Scanland Group/Company/Finance"]
CATEGORY: [subfolder name]
CONFIDENCE: [high/medium/low]
REASON: [what text you read in the image that led to this decision]"""

    api_client = get_client()
    
    response = api_client.messages.create(
        model=config.AI_MODEL,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    )
    
    text = response.content[0].text.strip()
    
    # Parse response (same format as categorize_file)
    result = {}
    for line in text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip().lower().replace(' ', '_')] = value.strip()
    
    # Resolve client info
    client_id_raw = result.get('client_id', 'none')
    client_id = None
    client_code = None
    
    if client_id_raw and client_id_raw.lower() not in ['none', 'unknown', 'n/a', '']:
        try:
            client_id = int(client_id_raw)
            if clients:
                client = next((c for c in clients if c['id'] == client_id), None)
                if client:
                    client_code = client['code']
        except (ValueError, TypeError):
            client_id = None
    
    return {
        'client_id': client_id,
        'client_code': client_code,
        'destination': result.get('destination', '_unsorted'),
        'category': result.get('category', '_unsorted'),
        'confidence': result.get('confidence', 'low'),
        'reason': result.get('reason', '')
    }


if __name__ == '__main__':
    # Test AI connection
    if config.ANTHROPIC_API_KEY:
        print("Testing Claude AI connection...")
        try:
            client = get_client()
            response = client.messages.create(
                model=config.AI_MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'Harbor AI Ready!' and nothing else."}]
            )
            print(f"✓ {response.content[0].text}")
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print("ANTHROPIC_API_KEY not configured")
