# Obsidian MCP Server

> **Connect Claude Desktop directly to your Obsidian vault.**  
> Ask Claude to read, write, search, and organise your notes - all from a single conversation.

---

## Video Tutorial

**New to MCP or not sure where to start?**  
Watch the full step-by-step tutorial on YouTube:

**[Watch the Tutorial → youtube.com/@dojicreates](https://www.youtube.com/@dojicreates/videos)**

---

## PDF Installation Guide

Want a printable, offline reference with screenshots for every step?

**[Get the PDF Guide → dojicreates.com](https://dojicreates.com/)**

The guide covers installation, configuration, and example prompts you can copy and use right away.

---

## What This Does

MCP (Model Context Protocol) is an open standard that lets AI assistants call external tools.
This server implements that standard and exposes your Obsidian vault as a set of tools Claude can use.

```
Claude Desktop  ←──── MCP (stdio) ────→  server.py  ←── file I/O ──→  Obsidian Vault
```

- Runs **100% locally** - no cloud service, no Obsidian plugin, no API keys
- Claude can only access files inside your vault - nothing else on your machine
- Works on **Windows and macOS**

---

## Folder Structure

```
mcp/
├── .venv/              ← isolated Python environment (created during setup)
├── server.py           ← the MCP server
├── config.json         ← your vault path goes here (not committed to git)
├── requirements.txt    ← Python dependencies
├── start_server.bat    ← optional: run the server manually on Windows
└── README.md           ← this file
```

---

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/) installed
- [Claude Desktop](https://claude.ai/download) installed
- An [Obsidian](https://obsidian.md/) vault on your machine

---

## Setup (5 minutes)

### Step 1 - Download this project

Click **Code → Download ZIP** on this page and extract it anywhere on your machine,  
or clone it with git:

```bash
git clone https://github.com/YOUR_USERNAME/obsidian-mcp-server.git
cd obsidian-mcp-server
```

---

### Step 2 - Create the Python virtual environment

Open a terminal inside the project folder and run:

**Windows (PowerShell or Command Prompt):**
```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

### Step 3 - Set your vault path

Open `config.json` and replace the placeholder with the real path to your Obsidian vault:

```json
{
  "vault_path": "C:/Users/YOUR_USERNAME/Documents/YourVaultName"
}
```

**How to find your vault path in Obsidian:**  
`Settings → Files and links → Vault path` (shown at the top of that section).

> Use forward slashes `/` even on Windows, or escape backslashes with `\\`.

> `config.json` is listed in `.gitignore` - it will **not** be pushed to GitHub, keeping your personal path private.

---

### Step 4 - Connect Claude Desktop

Claude Desktop reads its MCP server list from a config file.

**Find the config file:**

| OS      | Location |
|---------|----------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |

Open that file in any text editor. If it does not exist, create it.

**Add this block**, replacing the paths with the actual location of your project folder:

**Windows example:**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "C:\\Users\\YOUR_USERNAME\\path\\to\\mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YOUR_USERNAME\\path\\to\\mcp\\server.py"],
      "env": {}
    }
  }
}
```

**macOS example:**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/Users/YOUR_USERNAME/path/to/mcp/.venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/path/to/mcp/server.py"],
      "env": {}
    }
  }
}
```

> If the file already has other MCP servers, add the `"obsidian": { ... }` block inside the existing `"mcpServers"` object. Do not create a second `"mcpServers"` key.

**Save the file, then fully quit and reopen Claude Desktop.**  
On Windows: right-click the system tray icon → Quit, then relaunch.

---

### Step 5 - Verify it works

In Claude Desktop, start a new conversation and type:

> "List all my notes"

or

> "Show me the vault structure"

You should see a tool icon appear in the chat interface - that means Claude is connected to your vault.

---

## Available Tools

| Tool | What it does |
|------|-------------|
| `read_note(path)` | Read the full content of a note |
| `write_note(path, content)` | Create or overwrite a note |
| `append_to_note(path, content)` | Add text to the end of a note |
| `delete_note(path)` | Permanently delete a note |
| `list_notes(folder?)` | List all `.md` files (optionally inside a folder) |
| `search_notes(query, folder?, case_sensitive?)` | Full-text / regex search across notes |
| `get_vault_structure(max_depth?)` | Tree view of folders and files |
| `move_note(source, destination)` | Move or rename a note |
| `get_or_create_daily_note(date?)` | Get today's daily note; creates it from a template if absent |

All paths are **relative to the vault root**.  
Example: `"Ideas/Project Alpha.md"` - not the full system path.

---

## Example Prompts

```
"Search my notes for anything about machine learning"

"Create a note called Meeting Notes in my Work folder with today's action items"

"Add a task to my daily note: review project proposal"

"Show me everything in my Projects folder"

"Move my draft essay from Drafts/Essay.md to Published/Essay.md"
```

---

## Changing the Vault Path

Edit `config.json` and update `vault_path`. Restart Claude Desktop after saving.

Alternatively, you can skip `config.json` entirely and set an environment variable:

```
OBSIDIAN_VAULT_PATH=C:/Users/YOUR_USERNAME/Documents/YourVaultName
```

The environment variable takes priority over `config.json`.

---

## Troubleshooting

### Claude doesn't show the tool icon / server not found

1. Double-check the paths in `claude_desktop_config.json` - use double backslashes `\\` on Windows.
2. Make sure you fully quit Claude Desktop (not just closed the window) and relaunched it.
3. Test the server manually by opening a terminal and running:
   ```
   # Windows
   .venv\Scripts\python.exe server.py

   # macOS / Linux
   .venv/bin/python server.py
   ```
   It should print nothing and wait - that means it is working. Press `Ctrl+C` to stop.

### "Vault path not set" error

`config.json` is missing or `vault_path` is empty. Make sure `config.json` exists in the same folder as `server.py` and contains a valid path.

### "Path escapes the vault root" error

You passed an absolute path instead of a vault-relative path.  
Use `"Ideas/note.md"` not `"C:/Users/.../Ideas/note.md"`.

### Notes not showing up

Make sure `vault_path` points to the **root** of your vault - the folder that contains the `.obsidian` hidden folder, not a subfolder inside it.

### Re-installing dependencies

If you ever delete `.venv` or move the project to a new folder, run setup again:

```powershell
# Windows
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## How It Works (Technical)

`server.py` uses the **FastMCP** helper from Anthropic's `mcp` Python SDK.

- Each function decorated with `@mcp.tool()` becomes a callable tool in Claude.
- Claude Desktop launches `python server.py` as a child process when needed.
- Communication happens over **stdin/stdout** using JSON-RPC - no network port is opened.
- No authentication is required. Everything stays on your local machine.

Built using Anthropic's official MCP Python SDK (FastMCP).

```
Claude Desktop
  │
  ├─[spawn]──→ python server.py
  │
  ├─[stdin]──→ {"method":"tools/call","params":{"name":"read_note","arguments":{"path":"..."}}}
  │
  └─[stdout]←─ {"result":{"content":[{"type":"text","text":"..."}]}}
```

---

## Security

- The server only accesses files **inside** your vault directory. Any path that tries to escape (e.g. `../../sensitive-file`) is blocked at the code level.
- No data is sent anywhere - everything runs locally.
- Claude cannot execute shell commands or access anything outside the vault.

---

## License

MIT - free to use, modify, and distribute.

---

*Made with care. If this helped you, consider sharing it or leaving a star on GitHub.*  
*More tools and tutorials at [dojicreates.com](https://dojicreates.com/)*
