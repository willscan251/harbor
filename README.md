# Harbor

**The Business Management System** by Scanland & Co

Harbor is a comprehensive business management platform for The Scanland Group (TSG) and its parent company Scanland & Co. It manages clients, documents, meetings, tasks, and integrates with Microsoft SharePoint, Zoom, and Zoho Books.

## Architecture

```
harbor/
├── src/                    ← Next.js frontend + API routes
│   ├── app/
│   │   ├── dashboard/      ← Staff interface (harbor.thescanlandgroup.com)
│   │   ├── portal/         ← Client interface (portal.thescanlandgroup.com)
│   │   └── api/            ← Backend API routes
│   ├── components/
│   └── lib/                ← Database, auth, utilities
├── prisma/                 ← Database schema & migrations
├── services/               ← Python services (file watcher, AI, SharePoint)
│   ├── ai_processor.py
│   ├── integrations/
│   │   ├── file_watcher.py
│   │   ├── sharepoint.py
│   │   ├── zoom.py
│   │   └── zoho.py
│   └── manage_aliases.py
└── docs/                   ← Documentation
```

## Quick Start

```bash
# 1. Install Node.js dependencies
npm install

# 2. Set up environment
cp .env.local.example .env.local
# Edit .env.local with your API keys

# 3. Initialize database
npx prisma db push
npm run db:seed

# 4. Start development server
npm run dev
# Open http://localhost:3000

# 5. Start file watcher (separate terminal)
cd services
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python integrations/file_watcher.py start
```

## Development Commands

| Command | What it does |
|---------|-------------|
| `npm run dev` | Start Next.js dev server |
| `rm -rf .next && npm run dev` | Clear cache and restart (use when things get weird) |
| `npx prisma studio` | Open database browser |
| `npx prisma db push` | Push schema changes to database |
| `npm run db:seed` | Seed database with initial data |
| `npm run build` | Build for production |
| `npm run filewatcher` | Start Python file watcher |

## URLs

| URL | Purpose |
|-----|---------|
| `harbor.thescanlandgroup.com` | Staff dashboard |
| `portal.thescanlandgroup.com` | Client portal |
| `localhost:3000` | Local development |
| `localhost:3000/portal` | Local client portal |

## Deployment (Railway)

```bash
# Build and deploy
railway up

# Set environment variables in Railway dashboard
# Configure custom domains:
#   harbor.thescanlandgroup.com
#   portal.thescanlandgroup.com
```

## Python Services

The file watcher, AI document processor, and SharePoint integration run as Python services alongside the Next.js app. They share the same database.

```bash
cd services
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Authenticate SharePoint
python integrations/sharepoint.py auth

# Manage client aliases
python manage_aliases.py list
python manage_aliases.py add <client_id> "Alias Name"

# Process files
python integrations/file_watcher.py start
```
