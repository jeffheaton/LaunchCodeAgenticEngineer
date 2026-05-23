# Module 2 — LaunchCode Agentic Engineer

Docker development environment for LaunchCode's **Agentic Programming** course, Module 2. Extends the Module 1 environment with:

- **Slack MCP server** — lets Claude Code prompts read and post to Slack
- **Gmail MCP server** — lets Claude Code prompts read and send email
- **Pre-configured skills** — custom slash commands available inside Claude Code

## Quick Start

Build and run locally:

```bash
cd module_2
docker build -t agentic_engineer_2 .
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  agentic_engineer_2
```

Or pull the pre-built image from DockerHub:

```bash
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  heatonresearch/agentic_engineer_2:latest
```

Full setup with Slack and Gmail (reads credentials from your shell environment):

```bash
docker run -it --rm \
  -p 8501:8501 -p 8502:8502 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -e SLACK_TEAM_ID=$SLACK_TEAM_ID \
  -v "$PWD":/workspace \
  -v "$HOME/.gmail-mcp":/root/.gmail-mcp \
  heatonresearch/agentic_engineer_2:latest
```

Place `credentials.json` (from Google Cloud Console) in `$PWD` before running. The Gmail MCP will trigger OAuth on first use and persist the token in `~/.gmail-mcp/`.

## Build

```bash
docker build -t agentic_engineer_2 .
```

Force a complete rebuild (no cached layers):

```bash
docker build --no-cache -t agentic_engineer_2 .
```

## Run

### With a local workspace (recommended)

```bash
# macOS / Linux
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  agentic_engineer_2

# Windows (PowerShell)
docker run -it --rm -p 8501:8501 -p 8502:8502 `
  -e SLACK_BOT_TOKEN=xoxb-your-token `
  -e SLACK_TEAM_ID=T0123456 `
  -v "${PWD}:/workspace" `
  agentic_engineer_2
```

Files created or edited inside `/workspace` are saved to your local folder and persist after the container exits.

### Without a local workspace

```bash
docker run -it --rm -p 8501:8501 agentic_engineer_2
```

Any files created inside the container will be lost when it exits.

---

## MCP Servers

MCP (Model Context Protocol) servers extend Claude Code so that prompts can take real-world actions — posting to Slack, reading email, etc. — without writing any extra code. Both servers are pre-installed as global npm packages and pre-configured in `/root/.claude/settings.json` inside the image.

### Slack MCP Server

**Package:** `@modelcontextprotocol/server-slack`

**Required environment variables** (pass with `-e` at `docker run`):

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token from your Slack App (`xoxb-…`) |
| `SLACK_TEAM_ID` | Your Slack workspace ID (found in workspace settings) |

**Getting a Slack Bot Token:**

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2. Under **OAuth & Permissions**, add Bot Token Scopes: `channels:read`, `chat:write`, `channels:history`, `users:read`.
3. Install the app to your workspace and copy the **Bot User OAuth Token**.
4. Copy your workspace's **Team ID** from the workspace URL or settings.

**What it enables:** Claude Code prompts can list channels, read message history, post messages, and look up users in your Slack workspace.

### Gmail MCP Server

**Package:** `@gongrzhe/server-gmail-autoauth-mcp`

**Setup (OAuth):**

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API**.
3. Create OAuth 2.0 credentials (Desktop App type) and download `credentials.json`.
4. Place `credentials.json` in your workspace directory (mounted at `/workspace`).
5. On first use, the MCP server will open an OAuth flow and save a token. To persist the token across container restarts, mount the credentials directory:

```bash
docker run -it --rm -p 8501:8501 \
  -v "$PWD":/workspace \
  -v "$HOME/.gmail-mcp":/root/.gmail-mcp \
  agentic_engineer_2
```

**What it enables:** Claude Code prompts can read, search, and send Gmail messages on behalf of the authenticated user.

---

## Skills

Skills are custom slash commands available inside Claude Code. They are defined in `settings.json` (copied to `/root/.claude/settings.json` during the image build) and invoked by typing `/skill-name` in a Claude Code session.

### Pre-installed Skills

| Skill | Description |
|---|---|
| `/send-slack-message` | Send a message to a Slack channel via the Slack MCP server |
| `/check-gmail` | Retrieve and summarize recent unread Gmail messages |
| `/send-email` | Draft and send an email via the Gmail MCP server |
| `/summarize-session` | Generate a bullet-point summary of the current work session |

### Adding Your Own Skills

Edit `settings.json` before building the image, or modify `/root/.claude/settings.json` inside a running container:

```json
{
  "skills": [
    {
      "name": "my-skill",
      "description": "What this skill does",
      "prompt": "The full prompt Claude will execute when /my-skill is invoked."
    }
  ]
}
```

Rebuild the image after editing `settings.json` so the changes are baked in:

```bash
docker build -t agentic_engineer_2 .
```

---

## Gmail API Credentials (Python SDK)

In addition to the MCP server, the Python `google-api-python-client` library is available for direct API use in your code.

Place `credentials.json` (from Google Cloud Console) in your workspace directory. On first run it triggers OAuth and saves `token.json`. Reference it in code as:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
```

Keep both files out of source control:

```
# .gitignore
credentials.json
token.json
```

---

## Running Streamlit Apps

From inside the container:

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Build & Deploy to DockerHub

This section covers the full workflow for building the image and publishing it to DockerHub so students can pull it without building locally.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A DockerHub account (free at [hub.docker.com](https://hub.docker.com))
- Logged in to DockerHub on your machine:

```bash
docker login
```

### Step 1 — Build and tag for DockerHub

Build the image and tag it with your DockerHub username and repository name. Replace `heatonresearch` with your DockerHub username if different.

```bash
cd module_2
docker build -t heatonresearch/agentic_engineer_2:latest .
```

To tag a specific version number alongside `latest` (recommended so students can pin to a known-good version):

```bash
docker build \
  -t heatonresearch/agentic_engineer_2:latest \
  -t heatonresearch/agentic_engineer_2:2.0 .
```

Force a full rebuild ignoring all cached layers:

```bash
docker build --no-cache \
  -t heatonresearch/agentic_engineer_2:latest \
  -t heatonresearch/agentic_engineer_2:2.0 .
```

### Step 2 — Push to DockerHub

```bash
docker push heatonresearch/agentic_engineer_2:latest
docker push heatonresearch/agentic_engineer_2:2.0
```

Both tags must be pushed separately. The `latest` tag is what students get by default when they don't specify a version.

### Step 3 — Verify the image is public

Visit `https://hub.docker.com/r/heatonresearch/agentic_engineer_2` and confirm the repository visibility is set to **Public** so students can pull without logging in.

### Pulling the image (students)

Once published, students can run the image directly without cloning the repo or building anything:

```bash
docker run -it --rm -p 8501:8501 -p 8502:8502 \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_TEAM_ID=T0123456 \
  -v "$PWD":/workspace \
  heatonresearch/agentic_engineer_2:latest
```
