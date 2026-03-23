# Scanland & Co Shared Drive — Setup & Usage Guide

## Overview

The Scanland & Co Shared Drive is hosted on Microsoft SharePoint and organized as follows:

```
📁 Scanland & Co/              ← Parent company files
│   ├── Finance/
│   ├── Legal/
│   ├── Admin/
│   └── Operations/
📁 The Scanland Group/         ← TSG subsidiary
│   ├── Clients/               ← One folder per client
│   │   ├── Baldwin ARC/
│   │   │   ├── Meeting Notes/
│   │   │   ├── Contracts/
│   │   │   ├── Proposals/
│   │   │   ├── Reports/
│   │   │   ├── Financials/
│   │   │   ├── Correspondence/
│   │   │   └── _NeedsFolder/
│   │   └── [Other clients]/
│   ├── Company/
│   │   ├── Finance/  ← TSG taxes, IRS docs, payroll
│   │   ├── Legal/    ← TSG contracts, insurance
│   │   ├── HR/       ← Resumes, employee docs
│   │   └── Admin/    ← Internal memos
│   ├── Marketing/
│   ├── Resources/
│   └── Archive/
📁 Harbor Inbox/               ← Drop files here for auto-sorting
```

**SharePoint Site URL:** https://scanland.sharepoint.com/sites/TheScanlandGroup

---

## Permissions

| Person   | Role            | Access                                                       |
|----------|-----------------|--------------------------------------------------------------|
| Will     | Admin           | Full access to everything                                    |
| Patricia | Owner/Principal | Full access to everything                                    |
| Danny    | Staff (Limited) | Tuskegee client folder only under The Scanland Group/Clients |

### Setting Permissions in SharePoint

**To restrict Danny to Tuskegee only:**

1. Go to https://scanland.sharepoint.com/sites/TheScanlandGroup
2. Click the gear icon (top right) → **Site permissions**
3. Make sure Danny is **NOT** in the Members or Owners group. Remove him if he is.
4. Navigate to: Documents → The Scanland Group → Clients → Tuskegee
5. Click the **ⓘ** (info) icon on the Tuskegee folder → **Manage access**
6. Click **Grant Access** → type Danny's email → select **Can edit** → click **Grant**
7. Danny can now ONLY see the Tuskegee folder

**To give Patricia full access:**

1. Same Site permissions page
2. Add Patricia to the **Owners** group (or Members with edit rights)

---

## Setting Up the Shared Drive on Your Computer

### Mac Setup

**Step 1: Install OneDrive**
- Download from the Mac App Store or https://www.onedrive.live.com/download
- Install and open the app

**Step 2: Sign In**
- Open OneDrive from your Applications or menu bar
- Sign in with your Microsoft 365 account (e.g., will@scanland.org)
- If prompted, choose "Work or School account"

**Step 3: Sync SharePoint to Finder**
- Open Safari/Chrome and go to: https://scanland.sharepoint.com/sites/TheScanlandGroup
- Click **Documents** in the left sidebar
- Click the **Sync** button in the top toolbar
- Your browser will ask "Open OneDrive?" — click **Allow** or **Open**
- OneDrive will begin syncing. You'll see a progress notification.

**Step 4: Find it in Finder**
- Open Finder
- In the left sidebar under your OneDrive locations, you'll see: **The Scanland Group — Documents**
- This contains all the folders you have permission to see

**Step 5: Add to Favorites**
- Drag "The Scanland Group — Documents" from the sidebar to the **Favorites** section
- Drag the **Harbor Inbox** folder from your Desktop to Favorites too
- Now both are one click away

**Step 6 (Optional): Choose what syncs**
- Click the OneDrive icon in your Mac menu bar
- Click the gear icon → **Preferences** → **Account** → **Choose Folders**
- Uncheck folders you don't need locally to save disk space

### Windows Setup

**Step 1: OneDrive is Pre-Installed**
- OneDrive comes with Windows 10/11
- If not signed in: click the OneDrive cloud icon in the system tray → Sign in

**Step 2: Sign In**
- Sign in with your Microsoft 365 account
- Choose "Work or School account"

**Step 3: Sync SharePoint to File Explorer**
- Open Edge/Chrome and go to: https://scanland.sharepoint.com/sites/TheScanlandGroup
- Click **Documents** in the left sidebar
- Click the **Sync** button in the toolbar
- Allow it to open OneDrive
- Files will begin syncing

**Step 4: Find it in File Explorer**
- Open File Explorer
- In the left sidebar, you'll see the SharePoint library under your organization name
- It appears as: **The Scanland Group — Documents**

**Step 5: Pin to Quick Access**
- Right-click the synced folder → **Pin to Quick access**
- Do the same for Harbor Inbox

---

## Using the Harbor Inbox

The Harbor Inbox is the drop zone for automatic file sorting. Here's how it works:

### Workflow

1. **Drop a file** into your Harbor Inbox folder (in Finder or File Explorer)
2. **Harbor's AI reads the file** — extracts text from PDFs, Word docs, Excel files, and even reads images
3. **Harbor determines where it goes** — matches it to a client, reads the content, and picks the right folder
4. **File is uploaded** to the correct SharePoint folder automatically
5. **Original is moved** to Harbor Inbox/_Processed on your computer

### What Harbor Can Sort

| File Type | How Harbor Reads It                        |
|-----------|--------------------------------------------|
| PDF       | Extracts text from first 5 pages           |
| Word      | Reads paragraphs and tables                |
| Excel     | Reads first 3 sheets, 50 rows each         |
| Images    | Uses AI vision to read text in the image   |
| Text/CSV  | Reads directly                             |

### Tips for Best Results

- **Name files descriptively** — "Baldwin ARC 2026 Contract.pdf" is much better than "Document1.pdf"
- **Let Harbor read the content** — even with a vague filename, Harbor reads inside the file to determine where it belongs
- **Check _Processed** — after files are sorted, originals go to Harbor Inbox/_Processed
- **Check _unsorted** — if Harbor can't determine where a file goes, it lands in uploads/_unsorted for manual review
- **Add aliases** — if Harbor keeps missing a program name, tell Will to add it as an alias (e.g., "Carmita's Kitchen" → Community Connect CDC)

### What Each Person's Inbox Handles

| Person   | Inbox Scope                                              |
|----------|----------------------------------------------------------|
| Will     | All folders — Scanland & Co, The Scanland Group, everything |
| Patricia | The Scanland Group folders she has access to             |
| Danny    | Tuskegee client folder only                              |

---

## Accessing Files on Your Phone

### iPhone/iPad
1. Download the **OneDrive** app from the App Store
2. Sign in with your Microsoft 365 account
3. Tap **Shared** → **Shared Libraries** → **The Scanland Group**
4. All your permitted folders appear here

### Android
1. Download the **OneDrive** app from Google Play
2. Sign in with your Microsoft 365 account
3. Tap **Shared** → **Shared Libraries** → **The Scanland Group**

---

## Troubleshooting

**Files not syncing?**
- Check the OneDrive icon in your menu bar (Mac) or system tray (Windows)
- If there's a warning icon, click it for details
- Common fix: pause and resume sync

**Can't see a folder?**
- You may not have permission. Ask Will to check your SharePoint access.

**Harbor sorted a file wrong?**
- Move the file manually in SharePoint to the correct folder
- Tell Will the program/org name so he can add it as an alias for next time

**Sync is slow?**
- Large files take time. Check OneDrive sync progress.
- Choose to sync only folders you need (Preferences → Choose Folders)
