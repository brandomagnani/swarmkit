# SwarmKit Python SDK

Run terminal-based AI agents in secure sandboxes with built-in observability.

> See the [main README](../README.md) for installation and API keys.
>
> **Note:** Requires [Node.js 18+](https://nodejs.org/) (the SDK uses a lightweight Node.js bridge).

---

## 1. Quick Start

```bash
# .env

# SwarmKit gateway key (dashboard.swarmlink.ai)
SWARMKIT_API_KEY=sk-...

# Composio integrations (app.composio.dev)
COMPOSIO_API_KEY=...
```

SwarmKit auto-resolves API keys from environment variables.

```python
import os
from swarmkit import SwarmKit, AgentConfig, ComposioSetup, ComposioConfig

swarmkit = SwarmKit(
    config=AgentConfig(
        type='codex',
        api_key=os.getenv('SWARMKIT_API_KEY'),
    ),
    session_tag_prefix='my-app',
    system_prompt='You are Swarm, a powerful AI agent. You can execute code, browse the web, manage files, and solve complex tasks.',
    skills=['pdf', 'docx', 'pptx', 'dev-browser'],
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['gmail', 'notion', 'exa']),
    ),
)

result = await swarmkit.run(
    prompt='Go to Hacker News top posts. Spawn 5 parallel sub-agents to screenshot each of the top 5 posts.'
)

print(result.stdout)

output = await swarmkit.get_output_files()
for name, content in output.files.items():
    print(name)

# Once done, destroy sandbox
await swarmkit.kill()
```

- **Tracing:** When using `SWARMKIT_API_KEY`, every run is automatically logged to [dashboard.swarmlink.ai/traces](https://dashboard.swarmlink.ai/traces) for observability and replay. Optionally use `session_tag_prefix` to label your agent session for easy filtering.

## 1.1 Authentication

| | Gateway Mode | BYOK Mode |
|---|---------|---------------|
| Setup | `SWARMKIT_API_KEY` | Model provider keys + [`E2B_API_KEY`](https://e2b.dev) |
| Observability | [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai) | `~/.swarmkit/observability/` |
| Billing | Swarmlink | Your provider accounts |

---

### 1.1.1 Gateway Mode

Get API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai).

```bash
# .env
SWARMKIT_API_KEY=sk-...
```

```python
import os
from swarmkit import SwarmKit, AgentConfig

swarmkit = SwarmKit(
    config=AgentConfig(
        type='claude',
        api_key=os.getenv('SWARMKIT_API_KEY'),
    ),
)

await swarmkit.run(prompt='Hello')
```

---

### 1.1.2 BYOK Mode

Use your own provider keys. Requires [`E2B_API_KEY`](https://e2b.dev) for sandbox.

```bash
# .env
ANTHROPIC_API_KEY=sk-...
E2B_API_KEY=e2b_...
```

```python
import os
from swarmkit import SwarmKit, AgentConfig, E2BProvider

sandbox = E2BProvider(
    api_key=os.getenv('E2B_API_KEY'),
)

swarmkit = SwarmKit(
    config=AgentConfig(
        type='claude',
        provider_api_key=os.getenv('ANTHROPIC_API_KEY'),
    ),
    sandbox=sandbox,
)
```

---

### BYO Claude Max Subscription

```bash
# Run in terminal, follow login steps → receive token:
claude --setup-token

# ✓ Long-lived authentication token created successfully!
# Your OAuth token (valid for 1 year): sk-ant-...
```

```bash
# .env
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-...
E2B_API_KEY=e2b_...
```

```python
import os
from swarmkit import SwarmKit, AgentConfig, E2BProvider

sandbox = E2BProvider(
    api_key=os.getenv('E2B_API_KEY'),
)

swarmkit = SwarmKit(
    config=AgentConfig(
        type='claude',
        oauth_token=os.getenv('CLAUDE_CODE_OAUTH_TOKEN'),
    ),
    sandbox=sandbox,
)
```

---

### Auto-resolve from Environment

Set env vars and the SDK picks them up automatically—no need to pass explicitly. See [Agent Reference](#113-agent-reference) below for env var names.

### 1.1.3 Agent Reference

| type | models | default | env var (BYOK) |
|------|--------|---------|----------------|
| `'claude'` | `'opus'` `'sonnet'` `'haiku'` | `'opus'` | `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` |
| `'codex'` | `'gpt-5.2'` `'gpt-5.2-codex'` `'gpt-5.1-codex-max'` `'gpt-5.1-mini'` | `'gpt-5.2'` | `OPENAI_API_KEY` |
| `'gemini'` | `'gemini-3-pro-preview'` `'gemini-3-flash-preview'` `'gemini-2.5-pro'` `'gemini-2.5-flash'` `'gemini-2.5-flash-lite'` | `'gemini-3-flash-preview'` | `GEMINI_API_KEY` |
| `'qwen'` | `'qwen3-coder-plus'` `'qwen3-vl-plus'` | `'qwen3-coder-plus'` | `OPENAI_API_KEY` |

Agent-specific options: `reasoning_effort` (Codex: `'low'` `'medium'` `'high'` `'xhigh'`), `betas` (Claude Sonnet: `['context-1m-2025-08-07']`)

### Agent Examples

```bash
# .env - set env vars for auto-pickup
ANTHROPIC_API_KEY=sk-...   # claude
OPENAI_API_KEY=sk-...      # codex, qwen
GEMINI_API_KEY=...         # gemini
E2B_API_KEY=e2b_...        # sandbox
```

```python
# claude (auto-picks ANTHROPIC_API_KEY + E2B_API_KEY)
swarmkit = SwarmKit(
    config=AgentConfig(type='claude'),
)

swarmkit = SwarmKit(
    config=AgentConfig(type='claude', model='opus'),
)

swarmkit = SwarmKit(
    config=AgentConfig(
        type='claude',
        model='sonnet',
        betas=['context-1m-2025-08-07'],
    ),
)
```

```python
# codex (auto-picks OPENAI_API_KEY + E2B_API_KEY)
swarmkit = SwarmKit(
    config=AgentConfig(type='codex'),
)

swarmkit = SwarmKit(
    config=AgentConfig(type='codex', model='gpt-5.2-codex'),
)

swarmkit = SwarmKit(
    config=AgentConfig(type='codex', reasoning_effort='high'),
)
```

```python
# gemini (auto-picks GEMINI_API_KEY + E2B_API_KEY)
swarmkit = SwarmKit(
    config=AgentConfig(type='gemini'),
)

swarmkit = SwarmKit(
    config=AgentConfig(type='gemini', model='gemini-3-pro-preview'),
)
```

```python
# qwen (auto-picks OPENAI_API_KEY + E2B_API_KEY)
swarmkit = SwarmKit(
    config=AgentConfig(type='qwen'),
)

swarmkit = SwarmKit(
    config=AgentConfig(type='qwen', model='qwen3-coder-plus'),
)
```

---

## 2. Full Configuration

```python
import os
from swarmkit import SwarmKit, AgentConfig, E2BProvider, ComposioSetup, ComposioConfig

# Sandbox provider (auto-resolved from E2B_API_KEY, or explicit)
sandbox = E2BProvider(
    api_key=os.getenv('E2B_API_KEY'),   # (optional) Auto-resolves from E2B_API_KEY env var
    timeout_ms=3600000,                  # (optional) Default sandbox timeout (default: 1 hour)
)
```

```python
swarmkit = SwarmKit(

    # Agent configuration (optional if SWARMKIT_API_KEY set, defaults to claude)
    config=AgentConfig(
        type='codex',                        # 'claude' | 'codex' | 'gemini' | 'qwen' - defaults to 'claude'
        model='gpt-5.2-codex',               # (optional) Uses default if omitted
        reasoning_effort='medium',           # (optional) 'low' | 'medium' | 'high' | 'xhigh' - Codex only
        # betas=['context-1m-2025-08-07'],   # (optional) Claude Sonnet only
        api_key=os.getenv('SWARMKIT_API_KEY'), # (optional) Gateway mode - auto-resolves from env
        # provider_api_key=os.getenv('ANTHROPIC_API_KEY'), # (optional) Direct mode (BYOK)
        # oauth_token=os.getenv('CLAUDE_CODE_OAUTH_TOKEN'), # (optional) Claude Max subscription
    ),

    # Sandbox provider (auto-resolved from E2B_API_KEY, or use sandbox from above)
    sandbox=sandbox,

    # (optional) Uploads to /home/user/workspace/context/ on first run
    context={
        'docs/readme.txt': 'User provided context...',
        'data.json': '{"key": "value"}',
    },

    # (optional) System prompt appended to default instructions
    system_prompt='You are a careful pair programmer.',

    # (optional) Schema for structured output (agent writes result.json, validated on get_output_files())
    # Accepts Pydantic models or JSON Schema dicts
    schema=MyPydanticModel,

    # (optional) Skills for the agent
    skills=['pdf', 'docx', 'pptx', 'dev-browser'],

    # (optional) Composio Tool Router for 1000+ integrations
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['gmail', 'notion', 'stripe']),
    ),

    # (optional) Prefix for observability logs
    session_tag_prefix='my-agent',

    # ─────────────────────────────────────────────────────────────
    # Advanced
    # ─────────────────────────────────────────────────────────────

    # (optional) MCP servers for agent tools
    mcp_servers={
        'exa': {
            'command': 'npx',
            'args': ['-y', 'mcp-remote', 'https://mcp.exa.ai/mcp'],
            'env': {'EXA_API_KEY': os.getenv('EXA_API_KEY')}
        }
    },

    # (optional) Environment variables injected into sandbox
    secrets={'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN')},

    # (optional) Uploads to /home/user/workspace/ on first run
    files={
        'scripts/setup.sh': '#!/bin/bash\necho hello',
    },
)
```

**Note:**
- Configuration parameters can be combined in any order.
- The sandbox is created on the first `run()` or `execute_command()` call (see below).
- Context files, workspace files, MCP servers, and system prompt are set up once on the first call.
- Using `sandbox_id` parameter to reconnect skips setup since the sandbox already exists.
- `schema` accepts both Pydantic model classes and JSON Schema dicts.

**McpServerConfig** — MCP server connection (STDIO or HTTP/SSE):
```python
{'command': str, 'args': list[str], 'env': dict[str, str], 'url': str}  # STDIO: command+args, HTTP: url
```

## Agent Skills

Skills extend agent capabilities with specialized tools and workflows. See [agentskills.io](https://agentskills.io/home) for the open standard.

```bash
# .env
SWARMKIT_API_KEY=sk-...
COMPOSIO_API_KEY=...
```

```python
from swarmkit import SwarmKit

swarmkit = SwarmKit(
    skills=['pptx', 'dev-browser'],
)

await swarmkit.run(prompt='Browse Hacker News top 5 articles and create a slide deck summarizing each')
```

### Documents
| Skill | Description | Source |
|-------|-------------|--------|
| `pdf` | Read, extract, and analyze PDF documents | [skills/pdf](https://github.com/brandomagnani/swarmkit/tree/main/skills/pdf) |
| `docx` | Create and edit Word documents | [skills/docx](https://github.com/brandomagnani/swarmkit/tree/main/skills/docx) |
| `pptx` | Create and edit PowerPoint presentations | [skills/pptx](https://github.com/brandomagnani/swarmkit/tree/main/skills/pptx) |
| `xlsx` | Create and edit Excel spreadsheets | [skills/xlsx](https://github.com/brandomagnani/swarmkit/tree/main/skills/xlsx) |

### Browser Automation
| Skill | Description | Source |
|-------|-------------|--------|
| `agent-browser` | CLI-based headless browser automation for AI agents | [skills/agent-browser](https://github.com/brandomagnani/swarmkit/tree/main/skills/agent-browser) |
| `dev-browser` | Browser automation with persistent page state | [skills/dev-browser](https://github.com/brandomagnani/swarmkit/tree/main/skills/dev-browser) |
| `webapp-testing` | Test web applications | [skills/webapp-testing](https://github.com/brandomagnani/swarmkit/tree/main/skills/webapp-testing) |

### Research & Analysis
| Skill | Description | Source |
|-------|-------------|--------|
| `content-research-writer` | Research and write content | [skills/content-research-writer](https://github.com/brandomagnani/swarmkit/tree/main/skills/content-research-writer) |
| `lead-research-assistant` | Research and qualify leads | [skills/lead-research-assistant](https://github.com/brandomagnani/swarmkit/tree/main/skills/lead-research-assistant) |
| `meeting-insights-analyzer` | Analyze meeting insights | [skills/meeting-insights-analyzer](https://github.com/brandomagnani/swarmkit/tree/main/skills/meeting-insights-analyzer) |
| `developer-growth-analysis` | Analyze developer growth metrics | [skills/developer-growth-analysis](https://github.com/brandomagnani/swarmkit/tree/main/skills/developer-growth-analysis) |
| `competitive-ads-extractor` | Extract and analyze competitor ads | [skills/competitive-ads-extractor](https://github.com/brandomagnani/swarmkit/tree/main/skills/competitive-ads-extractor) |

### Design & Media
| Skill | Description | Source |
|-------|-------------|--------|
| `canvas-design` | Canvas and design creation | [skills/canvas-design](https://github.com/brandomagnani/swarmkit/tree/main/skills/canvas-design) |
| `image-enhancer` | Enhance and process images | [skills/image-enhancer](https://github.com/brandomagnani/swarmkit/tree/main/skills/image-enhancer) |
| `theme-factory` | Create themes and styles | [skills/theme-factory](https://github.com/brandomagnani/swarmkit/tree/main/skills/theme-factory) |
| `video-downloader` | Download videos from URLs | [skills/video-downloader](https://github.com/brandomagnani/swarmkit/tree/main/skills/video-downloader) |
| `slack-gif-creator` | Create GIFs for Slack | [skills/slack-gif-creator](https://github.com/brandomagnani/swarmkit/tree/main/skills/slack-gif-creator) |

### Business & Productivity
| Skill | Description | Source |
|-------|-------------|--------|
| `file-organizer` | Organize files and directories | [skills/file-organizer](https://github.com/brandomagnani/swarmkit/tree/main/skills/file-organizer) |
| `invoice-organizer` | Organize and process invoices | [skills/invoice-organizer](https://github.com/brandomagnani/swarmkit/tree/main/skills/invoice-organizer) |
| `brand-guidelines` | Brand asset and guidelines management | [skills/brand-guidelines](https://github.com/brandomagnani/swarmkit/tree/main/skills/brand-guidelines) |
| `internal-comms` | Internal communications tools | [skills/internal-comms](https://github.com/brandomagnani/swarmkit/tree/main/skills/internal-comms) |
| `tailored-resume-generator` | Generate tailored resumes | [skills/tailored-resume-generator](https://github.com/brandomagnani/swarmkit/tree/main/skills/tailored-resume-generator) |
| `domain-name-brainstormer` | Brainstorm domain names | [skills/domain-name-brainstormer](https://github.com/brandomagnani/swarmkit/tree/main/skills/domain-name-brainstormer) |

### Development
| Skill | Description | Source |
|-------|-------------|--------|
| `mcp-builder` | Build MCP servers | [skills/mcp-builder](https://github.com/brandomagnani/swarmkit/tree/main/skills/mcp-builder) |
| `skill-creator` | Create new skills | [skills/skill-creator](https://github.com/brandomagnani/swarmkit/tree/main/skills/skill-creator) |
| `skill-share` | Share skills with others | [skills/skill-share](https://github.com/brandomagnani/swarmkit/tree/main/skills/skill-share) |
| `changelog-generator` | Generate changelogs from commits | [skills/changelog-generator](https://github.com/brandomagnani/swarmkit/tree/main/skills/changelog-generator) |
| `artifacts-builder` | Build artifacts and deliverables | [skills/artifacts-builder](https://github.com/brandomagnani/swarmkit/tree/main/skills/artifacts-builder) |

### Other
| Skill | Description | Source |
|-------|-------------|--------|
| `raffle-winner-picker` | Pick raffle winners randomly | [skills/raffle-winner-picker](https://github.com/brandomagnani/swarmkit/tree/main/skills/raffle-winner-picker) |

---

## Composio (Tool Router)

Access 1000+ integrations (GitHub, Gmail, Slack, etc.) via [Composio](https://composio.dev).

[Tool Router Overview](https://docs.composio.dev/tool-router/overview) — How Tool Router works and integration guide.

[Available Toolkits](https://docs.composio.dev/toolkits/introduction) — Browse all 1000+ supported integrations.

```bash
# .env
SWARMKIT_API_KEY=sk-...      # SwarmKit gateway key
COMPOSIO_API_KEY=...         # Get from https://app.composio.dev
```

```python
from swarmkit import SwarmKit, ComposioSetup

swarmkit = SwarmKit(
    composio=ComposioSetup(user_id='user_123'),  # All tools, in-chat OAuth
)

await swarmkit.run(prompt='Create a GitHub issue for the login bug')
```

### Authentication Paths

**1. In-chat auth (default)** — Composio prompts user to authenticate via agent output:
```python
from swarmkit import SwarmKit, ComposioSetup

swarmkit = SwarmKit(
    composio=ComposioSetup(user_id='user_123'),  # Agent prompts "Connect to GitHub" when needed
)

await swarmkit.run(prompt='Star my favorite repos on GitHub')
```

**2. API key auth** — Bypass OAuth for tools that support API keys:
```python
import os
from swarmkit import SwarmKit, ComposioSetup, ComposioConfig

swarmkit = SwarmKit(
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(
            toolkits=['stripe', 'sendgrid'],
            keys={
                'stripe': os.getenv('STRIPE_API_KEY'),
                'sendgrid': os.getenv('SENDGRID_API_KEY'),
            },
        ),
    ),
)

await swarmkit.run(prompt='List my recent Stripe payments')
```

**3. Manual OAuth (app UI)** — Get OAuth URL to show in your settings page:
```python
from swarmkit import SwarmKit, ComposioSetup, ComposioConfig

# Get OAuth URL for "Connect GitHub" button
result = await SwarmKit.composio.auth('user_123', 'github')
# Render: <a href={result.url}>Connect GitHub</a>

# Check connection status (simple)
status = await SwarmKit.composio.status('user_123')
# {'github': True, 'gmail': False, 'slack': True}

# Check single toolkit
is_github_connected = await SwarmKit.composio.status('user_123', 'github')
# True | False

# Get detailed connection info (with account IDs)
connections = await SwarmKit.composio.connections('user_123')
# [ComposioConnectionStatus(toolkit='github', connected=True, account_id='ca_...'), ...]

# Then use in agent (user already connected via UI)
swarmkit = SwarmKit(
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['github']),
    ),
)

await swarmkit.run(prompt='List my open PRs')
```

**4. White-label OAuth** — Use custom OAuth configs from [Composio dashboard](https://app.composio.dev):
```python
from swarmkit import SwarmKit, ComposioSetup, ComposioConfig

swarmkit = SwarmKit(
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(
            toolkits=['github'],
            auth_configs={'github': 'ac_your_custom_oauth_app'},
        ),
    ),
)

await swarmkit.run(prompt='Create a new private repo')
```

### Tool Filtering

```python
from swarmkit import SwarmKit, ComposioSetup, ComposioConfig

swarmkit = SwarmKit(
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(
            toolkits=['github', 'gmail', 'slack'],
            tools={
                'github': ['github_create_issue', 'github_list_repos'],  # Enable only these
                'gmail': {'disable': ['gmail_delete_email']},            # Disable dangerous tools
                'slack': {'tags': ['readOnlyHint']},                     # Filter by behavior tags
            },
        ),
    ),
)

await swarmkit.run(prompt='Send a Slack message about the GitHub issue')
```

### Type Reference

**ComposioSetup** — configuration for `composio=ComposioSetup(...)`:
```python
@dataclass
class ComposioSetup:
    user_id: str                                            # User's unique identifier
    config: Optional[ComposioConfig] = None                 # Optional configuration

@dataclass
class ComposioConfig:
    toolkits: Optional[List[str]] = None                    # e.g. ['gmail', 'notion', 'stripe']
    tools: Optional[Dict[str, ToolsFilter]] = None          # Per-toolkit tool filtering
    keys: Optional[Dict[str, str]] = None                   # API keys (bypasses OAuth)
    auth_configs: Optional[Dict[str, str]] = None           # Custom OAuth auth config IDs

ToolsFilter = Union[
    List[str],                                              # Enable only these tools
    EnableFilter,                                           # {'enable': [...]}
    DisableFilter,                                          # {'disable': [...]}
    TagsFilter,                                             # {'tags': [...]}
]
```

---

## 3. Runtime Methods

All runtime calls are `async` and return an `AgentResponse`:

```python
@dataclass
class AgentResponse:
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
```

### 3.1 run

Runs the agent with a given prompt.

```python
result = await swarmkit.run(
    prompt='Analyze the data and create a report',
    timeout_ms=15 * 60 * 1000,                # (optional) Default 1 hour
    background=False,                          # (optional) Run in background
)

print(result.exit_code)
print(result.stdout)
```

- If `timeout_ms` is omitted the agent uses the default of 3_600_000 ms (1 hour).
- If `background` is `True`, the call returns immediately while the agent continues running.

- Calling `run()` multiple times maintains the agent context / history.

### 3.2 execute_command

Runs a direct shell command in the sandbox working directory.

```python
# Run shell command directly in sandbox
result = await swarmkit.execute_command(
    command='pytest',
    timeout_ms=10 * 60 * 1000,                # (optional) Default 1 hour
    background=False,                          # (optional) Run in background
)
```

### 3.3 Streaming events

Both `run()` and `execute_command()` stream output in real-time:

```python
# Raw output
swarmkit.on('stdout', lambda data: print(data, end=''))
swarmkit.on('stderr', lambda data: print(f'[ERR] {data}', end=''))

# Parsed output (recommended)
swarmkit.on('content', lambda event: print(event['update']))
```

**Events**:

| Event | Description |
|-------|-------------|
| `content` | Parsed ACP-style events (recommended) |
| `stdout` | Raw JSONL output |
| `stderr` | Stderr chunks |

**Content event structure** (`event['update']`):

| `sessionUpdate` | Description | Key Fields |
|-----------------|-------------|------------|
| `agent_message_chunk` | Text/image from agent | `content.type`, `content.text` |
| `agent_thought_chunk` | Reasoning/thinking (Codex/Claude) | `content.type`, `content.text` |
| `user_message_chunk` | User message echo (Gemini) | `content.type`, `content.text` |
| `tool_call` | Tool started | `toolCallId`, `title`, `kind`, `status`, `rawInput?`, `content?`, `locations?` |
| `tool_call_update` | Tool finished | `toolCallId`, `status?`, `title?`, `content?`, `locations?` |
| `plan` | TodoWrite updates | `entries[]` with `content`, `status`, `priority` |

All listeners are optional.

#### Building a Real-Time UI with Callbacks

When building interactive CLI applications with streaming, use a **stateful renderer class** with callbacks. The recommended pattern uses Rich's `Live` for tool status updates while printing messages directly:

```python
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

console = Console()

class StreamRenderer:
    def __init__(self):
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}           # tool_id -> {title, status, kind, raw_input}
        self.tool_order = []      # preserve tool ordering
        self.plan_entries = []    # [{content, status, priority}, ...]
        self.status_live = None

    def reset(self):
        self._stop_status_live()
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}
        self.tool_order = []
        self.plan_entries = []

    def handle_event(self, event: dict):
        """Main callback - register with swarmkit.on('content', ...)"""
        update = event.get("update", {})
        event_type = update.get("sessionUpdate")

        if event_type == "agent_message_chunk":
            content = update.get("content", {})
            if content.get("type") == "text":
                self.current_message += content.get("text", "")

        elif event_type == "agent_thought_chunk":
            # Reasoning/thinking from Codex or Claude
            content = update.get("content", {})
            if content.get("type") == "text":
                self.thought_buffer += content.get("text", "")

        elif event_type == "tool_call":
            self._flush_message()  # Print message before tool
            tool_id = update.get("toolCallId", "")
            if tool_id not in self.tools:
                self.tool_order.append(tool_id)
            self.tools[tool_id] = {
                'title': update.get("title", "Tool"),
                'kind': update.get("kind", "other"),  # read, edit, search, execute, think, fetch, switch_mode, other
                'status': update.get("status", "pending"),
                'raw_input': update.get("rawInput", {}),
            }
            self._refresh_status()

        elif event_type == "tool_call_update":
            tool_id = update.get("toolCallId", "")
            # Handle out-of-order: update may arrive before tool_call
            if tool_id not in self.tools:
                self.tool_order.append(tool_id)
                self.tools[tool_id] = {
                    'title': update.get("title", "Tool"),
                    'kind': "other",
                    'status': "pending",
                    'raw_input': {},
                }
            self.tools[tool_id]['status'] = update.get("status", "completed")
            self._refresh_status()

        elif event_type == "plan":
            # TodoWrite updates - list of {content, status, priority}
            self._flush_message()
            self.plan_entries = update.get("entries", [])
            self._render_plan()

    def _flush_message(self):
        if self.current_message.strip():
            console.print(Markdown(self.current_message))
            console.print()
            self.current_message = ""

    def _render_plan(self):
        """Render plan/todo entries"""
        if not self.plan_entries:
            return
        for entry in self.plan_entries:
            status = entry.get("status", "pending")
            content = entry.get("content", "")
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "○")
            style = {"completed": "green", "in_progress": "cyan", "pending": "dim"}.get(status, "dim")
            console.print(f"[{style}]{icon} {content}[/{style}]")
        console.print()

    def _render_status(self):
        """Render all tools as a Group - updates in place"""
        lines = []
        for tool_id in self.tool_order:
            tool = self.tools[tool_id]
            status = tool.get('status', 'pending')
            dot_style = "green" if status == 'completed' else "red" if status == 'failed' else "cyan"
            line = Text()
            line.append("● ", style=dot_style)
            line.append(f"{tool['title']}", style="white")
            lines.append(line)
        lines.append(Spinner("dots", style="cyan"))
        return Group(*lines) if lines else Text("")

    def _refresh_status(self):
        if self.status_live:
            self.status_live.update(self._render_status(), refresh=True)

    def _stop_status_live(self):
        if self.status_live:
            self.status_live.stop()
            self.status_live = None

    def start_live(self):
        self.status_live = Live(self._render_status(), console=console, refresh_per_second=12)
        self.status_live.start()

    def stop_live(self):
        self._stop_status_live()
        self._flush_message()
        # Optionally display collected thoughts
        if self.thought_buffer.strip():
            console.print("[dim]Reasoning:[/dim]")
            console.print(f"[dim italic]{self.thought_buffer}[/dim italic]")

# Usage:
renderer = StreamRenderer()
swarmkit.on("content", renderer.handle_event)

renderer.reset()
renderer.start_live()
await swarmkit.run(prompt="Your task here")
renderer.stop_live()
```

**Key patterns:**

1. **Handle all 5 event types** - `agent_message_chunk`, `agent_thought_chunk`, `tool_call`, `tool_call_update`, `plan`
2. **Flush messages before tools/plan** - Preserves correct interleaving order
3. **Track tools by ID** - `tool_call` (start) and `tool_call_update` (end) share `toolCallId`
4. **Handle out-of-order updates** - `tool_call_update` may arrive before `tool_call`
5. **Use `kind` for tool categorization** - `read`, `edit`, `search`, `execute`, `think`, `fetch`, `switch_mode`, `other`

> **Full production example:** See [`cookbooks/agent-python/ui.py`](../cookbooks/agent-python/ui.py) for styled formatting, tool content display, and advanced Live block management.

### 3.4 Upload: Local → Sandbox

**Format:** `{"destination": content}` — directories created automatically

| Method | Destination |
|--------|-------------|
| `upload_context()` | `/home/user/workspace/context/{path}` |
| `upload_files()` | `/home/user/workspace/{path}` |

```python
# Single file
await swarmkit.upload_context({'spec.json': json.dumps(data)})

# Multiple files
await swarmkit.upload_files({
    'scripts/setup.sh': '#!/bin/bash\necho hello',
    'data/input.csv': csv_bytes,
})

# From local directory (helper)
from swarmkit import read_local_dir
await swarmkit.upload_context(read_local_dir('./input', recursive=True))
```

> **Setup alternative:** Constructor parameters `context` and `files` use the same format but upload on first `run()` instead of immediately.

### 3.5 Download: Sandbox → Local

**Flow:** `get_output_files()` → `save_local_dir()`

```python
# Return type
@dataclass
class OutputResult:
    files: dict          # All files from output/ folder
    data: Any | None     # Parsed result.json (if schema was set via schema=)
    error: str | None    # Validation error message (if schema validation failed)
    raw_data: str | None # Raw result.json content when parse/validation failed (for debugging)
```

```python
from pydantic import BaseModel
from swarmkit import SwarmKit, save_local_dir

class ResultSchema(BaseModel):
    summary: str
    score: float

swarmkit = SwarmKit(
    config=AgentConfig(...),
    schema=ResultSchema,  # Agent will be prompted to write result.json
)

await swarmkit.run(prompt='Analyze and score the document')

output = await swarmkit.get_output_files(recursive=True)  # recursive=True for nested dirs

# Access all fields
save_local_dir('./output', output.files)  # Save files locally
print(output.data)                         # ResultSchema(summary='...', score=85.0)
print(output.error)                        # None (or validation error message)
```

- **`files`** — dict of all files from `output/` folder
- **`data`** — Parsed `result.json` validated against schema (None if no schema or validation failed). For Pydantic schemas, returns a model instance.
- **`error`** — Validation error message if schema validation failed (None otherwise)
- **`raw_data`** — Raw result.json content when parse/validation failed (for debugging)

Files created before the last `run()` or `execute_command()` are filtered out.

### 3.6 Session controls

```python
session_id = await swarmkit.get_session()  # Returns sandbox ID (str) or None

await swarmkit.pause()   # Suspends sandbox (stops billing, preserves state)
await swarmkit.resume()  # Reactivates same sandbox

await swarmkit.kill()    # Destroys sandbox; next run() creates a new sandbox

await swarmkit.set_session('existing-sandbox-id')  # Sets sandbox ID; reconnection happens on next run()
```

`sandbox_id` constructor parameter is equivalent to `set_session()` - use it during initialization to reconnect to an existing sandbox.

### 3.7 get_host

Expose a forwarded port:

```python
url = await swarmkit.get_host(8000)
print(f'Workspace service available at {url}')
```
---

## 4. Workspace Setup & Structured Output

Calling `run` or `execute_command` for the first time provisions a sandbox with the following filesystem:

```
/home/user/workspace/
├── context/     # Input files (read-only) provided by the user
├── scripts/     # Your code goes here
├── temp/        # Scratch space
├── output/      # Final deliverables
└── CLAUDE.md    # System prompt (or AGENT.md, GEMINI.md, QWEN.md depending on agent)
```

Files passed to `context` are uploaded to `context/`. Files passed to `files` are uploaded relative to the working directory.

## Filesystem Instructions
SwarmKit writes a default filesystem instructions to the agent's config file in the workspace (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, or `QWEN.md`):

```
## FILESYSTEM INSTRUCTIONS

You are running in a sandbox environment.

Present working directory: /home/user/workspace/

IMPORTANT - Directory structure:
/home/user/workspace/
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables

## OUTPUT RESULTS (DELIVERABLES) MUST BE SAVED to `output/` as files.
```

Any string passed to `system_prompt` is automatically appended to the agent's config file in the workspace (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, or `QWEN.md`) after this default.

## Structured Output

When you provide a `schema`, SwarmKit instructs the agent to write structured JSON output.

```python
from pydantic import BaseModel

class CREData(BaseModel):
    property_name: str
    units: int
    total_rent: float
    occupancy_rate: float

swarmkit = SwarmKit(
    schema=CREData,
    context={
        'rent_roll.pdf': open('rent_roll.pdf', 'rb').read(),
    },
)

await swarmkit.run(prompt='Extract CRE data from the rent roll')

output = await swarmkit.get_output_files()
print(output.data)  # CREData(property_name='...', units=120, ...)
```

When a schema is provided, `get_output_files()` automatically validates `output/result.json` and returns:

```python
@dataclass
class OutputResult:
    files: Dict[str, bytes]           # All output files
    data: Any | None                  # Parsed & validated result.json (None if failed)
    error: str | None                 # Validation/parse error message
    raw_data: str | None              # Raw result.json for debugging failed validation
```

```python
# Type-safe access to validated data
if output.data:
    print(output.data.property_name)  # Pydantic model instance
else:
    print(output.error)               # "Schema validation failed: ..."
    print(output.raw_data)            # Raw JSON for debugging
```

The SDK automatically appends the following to the agent's config file in the workspace (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, or `QWEN.md`):

~~~
## STRUCTURED OUTPUT

Your final result MUST be saved to `output/result.json` following this schema:

```json
{
  "type": "object",
  "properties": {
    "property_name": { "type": "string" },
    "units": { "type": "integer" },
    "total_rent": { "type": "number" },
    "occupancy_rate": { "type": "number" }
  },
  "required": ["property_name", "units", "total_rent", "occupancy_rate"]
}
```

You are free to:
- Reason through the problem step by step
- Read and analyze context files
- Use any available tools
- Process incrementally
- Create intermediate files in `temp/` or `scripts/`

But your final `output/result.json` MUST conform to the schema above.

### OUTPUT RESULTS (DELIVERABLES) MUST BE WRITTEN to `output/result.json` as files.
### Never just state results as text.
~~~

---

## 5. Cleaning up and session management

**Multi-turn conversations** (most common):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
)

await swarmkit.run(prompt='Analyze data.csv')
output = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Now create visualization')
output2 = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Export to PDF')
output3 = await swarmkit.get_output_files()

await swarmkit.kill()  # When done
```

**One-shot tasks** (automatic cleanup):

```python
async with swarmkit:
    result = await swarmkit.run(prompt='...')
    output = await swarmkit.get_output_files()
# Calls kill() automatically via __aexit__()
```

**Pause and resume** (same instance):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
)

await swarmkit.run(prompt='Start analysis')
await swarmkit.pause()  # Suspend billing, keep state
# Do other work...
await swarmkit.resume()  # Reactivate same sandbox
await swarmkit.run(prompt='Continue analysis')  # Session intact

await swarmkit.kill()  # Kill the Sandbox when done
```

**Save and reconnect** (different script/session):

```python
# Script 1: Save session for later
swarmkit = SwarmKit(
    config=AgentConfig(...),
)

await swarmkit.run(prompt='Start analysis')

session_id = await swarmkit.get_session()
# Save to file, database, environment variable, etc.
with open('session.txt', 'w') as f:
    f.write(session_id)

# Script 2: Reconnect to saved session
with open('session.txt') as f:
    saved_id = f.read()

swarmkit2 = SwarmKit(
    config=AgentConfig(...),
    sandbox_id=saved_id  # Reconnect
)

await swarmkit2.run(prompt='Continue analysis')  # Session continues from Script 1
```

**Switch between sandboxes** (same instance):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
)

# Work with first sandbox
await swarmkit.run(prompt='Analyze dataset A')
session_a = await swarmkit.get_session()

# Switch to different sandbox
await swarmkit.set_session('existing-sandbox-b-id')
await swarmkit.run(prompt='Analyze dataset B')  # Now working with sandbox B

# Switch back to first sandbox
await swarmkit.set_session(session_a)
await swarmkit.run(prompt='Compare results')  # Back to sandbox A
```

---

## 6. Observability

Full execution traces—including tool calls, file operations (read/write/edit), text responses, and reasoning chunks—are logged to your SwarmKit dashboard at **https://dashboard.swarmlink.ai/traces** for debugging and replay.

Additionally, every run and command is logged locally to structured JSON lines under `~/.swarmkit/observability/sessions`. File name format:

```
{tag}_{provider}_{sandboxId}_{agent}_{timestamp}.jsonl
```

- `{tag}` – `my-prefix-` + 16 random hex characters (e.g. `my-prefix-a1b2c3d4e5f6g7h8`)
- `{provider}` – the sandbox provider (e.g. `e2b`)
- `{sandboxId}` – the active sandbox ID
- `{agent}` – the agent type (`codex`, `claude`, `gemini`, `qwen`)
- `{timestamp}` – ISO timestamp with `:` and `.` replaced by `-`

Each file contains three entry types:

```json
{"_meta":{"tag":"my-prefix-a1b2c3d4","provider":"e2b","sandbox_id":"sbx_123","agent":"qwen","timestamp":"2025-10-26T20:15:17.984Z"}}
{"_prompt":{"text":"hello how are you?"}}
{"jsonrpc":"2.0","method":"session/update", ...}
```

- `_meta` – exactly one line per file (sandbox, agent, timestamp)
- `_prompt` – one line per `run()` call with the prompt text
- Raw JSON – every streamed payload (ACP notifications, stdout, etc.)

Attach your own prefix to make logs easy to search:

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    session_tag_prefix='my-project'
)

await swarmkit.run(prompt='Kick off analysis')

print(await swarmkit.get_session_tag())        # "my-project-ab12cd34"
print(await swarmkit.get_session_timestamp())  # Timestamp for first log file

await swarmkit.kill()                          # Flushes log file for sandbox A

await swarmkit.run(prompt='Start fresh')       # New sandbox → new log file

print(await swarmkit.get_session_tag())        # "my-project-f56789cd"
print(await swarmkit.get_session_timestamp())  # Timestamp for second log file
```

- `kill()` or `set_session()` flushes the current log; the next `run()` starts a
  fresh file with the new sandbox id.
- Long-running sessions (pause/resume or ACP auto-resume) keep appending to the
  current file, so you always have the full timeline.
- Logging is buffered inside the SDK, so it never blocks streaming output.

Use the tag together with the sandbox id to correlate logs with files saved in
`/output/`.

---

# Swarm Abstractions

Functional programming for AI agents: `map`, `filter`, `reduce`, `best_of`.

```python
from swarmkit import Swarm, SwarmConfig, AgentConfig, ComposioSetup, ComposioConfig
from pydantic import BaseModel  # Or use plain JSON Schema dicts instead

agent = AgentConfig(type='claude')

swarm = Swarm(SwarmConfig(
    agent=agent,                     # Default agent for all operations
    concurrency=4,                   # Max parallel sandboxes (default: 4)
    timeout_ms=3_600_000,            # Default timeout per worker (default: 1 hour)
    tag='my-pipeline',               # Tag prefix for observability
    skills=['pdf', 'dev-browser'],   # Default skills for all workers
    composio=ComposioSetup(          # Default Composio config for all workers
        user_id='user_123',
        config=ComposioConfig(toolkits=['gmail', 'notion']),
    ),
    mcp_servers={...},               # Default MCP servers for all workers
    retry=RetryConfig(               # Default retry config for all operations
        max_attempts=3,
        backoff_ms=1000,
        backoff_multiplier=2,
    ),
))
```

> **Defaults**: `agent`, `skills`, `composio`, `mcp_servers`, `timeout_ms`, and `retry` set here are inherited by all operations (`map`, `filter`, `reduce`, `best_of`). Pass these options to individual operations to override.

**SwarmConfig** — configuration for Swarm instance:
```python
SwarmConfig(
    agent=AgentConfig,
    skills=list[str],
    composio=ComposioSetup,
    mcp_servers=dict[str, McpServerConfig],
    concurrency=int,
    timeout_ms=int,
    tag=str,
    retry=RetryConfig,
)
```

| Option | Default | Notes |
|--------|---------|-------|
| `agent.type` | `'claude'` | Auto-resolved from env |
| `agent.model` | per type | `'opus'` (claude), `'gpt-5.2'` (codex), etc. |
| `skills` | `None` | Set here or per-operation |
| `composio` | `None` | Set here or per-operation |
| `mcp_servers` | `None` | Set here or per-operation |
| `concurrency` | `4` | Max parallel sandboxes |
| `timeout_ms` | `3_600_000` | 1 hour per worker |
| `tag` | `'swarm'` | Observability prefix |
| `retry` | `None` | Set here or per-operation |

**Minimal setup** — with `SWARMKIT_API_KEY` set (see [1.1 Authentication](#11-authentication)):

```python
from dotenv import load_dotenv
load_dotenv()  # If using .env file

from swarmkit import Swarm

swarm = Swarm()  # Auto-resolves agent (claude) and sandbox from env
```

**RetryConfig** — auto-retry on error with exponential backoff:
```python
RetryConfig(
    max_attempts=3,
    backoff_ms=1000,
    backoff_multiplier=2,
    retry_on=lambda r: r.status == 'error',        # Custom condition
    on_item_retry=lambda idx, attempt, error: ..., # Callback
)
```

**VerifyConfig** — LLM-as-judge verifies output, retries with feedback if failed:
```python
VerifyConfig(
    criteria='...',                                         # Required
    max_attempts=3,
    verifier_agent=AgentConfig(...),                        # Optional override
    verifier_skills=['pdf'],                                # Skills for verifier
    verifier_composio=ComposioSetup(...),                   # Composio config for verifier
    verifier_mcp_servers={...},                             # MCP servers for verifier
    on_worker_complete=lambda idx, attempt, status: ...,    # Callback
    on_verifier_complete=lambda idx, attempt, passed, feedback: ...,
)
```

## 1. Input Types

Swarm runs in **knowledge mode** by default—files are uploaded to `context/` in the sandbox.

**FileMap structure:**

```python
# FileMap: dict[path, content]
#   - path: str              → file path in context/ folder
#   - content: str | bytes   → file content

FileMap = dict[str, str | bytes]
```

---

**Case 1: One file per worker**

```python
# 3 workers, each gets 1 file
items: list[FileMap] = [
    {'report.txt': 'Q1 revenue...'},      # → Worker 0: context/report.txt
    {'report.txt': 'Q2 revenue...'},      # → Worker 1: context/report.txt
    {'report.txt': 'Q3 revenue...'},      # → Worker 2: context/report.txt
]

results = await swarm.map(
    items=items,
    prompt='Summarize this report',
)
```

---

**Case 2: Multiple files per worker**

```python
# 3 workers, each gets 2 files
items: list[FileMap] = [
    {                                       # → Worker 0:
        'doc1.pdf': open('./doc1.pdf', 'rb').read(),  #   context/doc1.pdf
        'doc2.pdf': open('./doc2.pdf', 'rb').read(),  #   context/doc2.pdf
    },
    {                                       # → Worker 1:
        'doc3.pdf': open('./doc3.pdf', 'rb').read(),  #   context/doc3.pdf
        'doc4.pdf': open('./doc4.pdf', 'rb').read(),  #   context/doc4.pdf
    },
    {                                       # → Worker 2:
        'doc5.pdf': open('./doc5.pdf', 'rb').read(),  #   context/doc5.pdf
        'doc6.pdf': open('./doc6.pdf', 'rb').read(),  #   context/doc6.pdf
    },
]

results = await swarm.map(
    items=items,
    prompt='Compare these two documents',
)
```

---

**Case 3: Entire folder per worker**

```python
from swarmkit import read_local_dir

# read_local_dir(path, recursive) → returns FileMap with all files
items: list[FileMap] = [
    read_local_dir('./project-a', recursive=True),   # → Worker 0: all files from project-a
    read_local_dir('./project-b', recursive=True),   # → Worker 1: all files from project-b
    read_local_dir('./project-c', recursive=True),   # → Worker 2: all files from project-c
]

results = await swarm.map(
    items=items,
    prompt='Review this codebase',
)
```

## 2. Abstractions

Two types of operations:

| Operation | Type | Description | Passes On |
|-----------|------|-------------|-----------|
| `best_of` | transform + select | `input` → `output` (best of N candidates) | winner output |
| `map` | transform | `input` → `output` (agent produces new data) | agent output |
| `filter` | gate | `input` → `input` (agent evaluates, condition decides) | original input + status (`success` \| `filtered`) |
| `reduce` | transform | `inputs` → `output` (agent synthesizes) | agent output |

**Transforms** produce new output files. **Filter** passes through original input files unchanged.

**BestOfConfig** — run N candidates in parallel, judge picks the best:
```python
BestOfConfig(
    n=int,
    judge_criteria=str,
    task_agents=list[AgentConfig],
    judge_agent=AgentConfig,
    skills=list[str],
    judge_skills=list[str],
    composio=ComposioSetup,
    judge_composio=ComposioSetup,
    mcp_servers=dict[str, McpServerConfig],
    judge_mcp_servers=dict[str, McpServerConfig],
    on_candidate_complete=Callable[[int, int, str], None],
    on_judge_complete=Callable[[int, int, str], None],
)
```

**VerifyConfig** — LLM-as-judge verifies output, retries with feedback if failed:
```python
VerifyConfig(
    criteria=str,
    max_attempts=int,
    verifier_agent=AgentConfig,
    verifier_skills=list[str],
    verifier_composio=ComposioSetup,
    verifier_mcp_servers=dict[str, McpServerConfig],
    on_worker_complete=Callable[[int, int, str], None],
    on_verifier_complete=Callable[[int, int, bool, str | None], None],
)
```

### 2.1 best_of

Run N agents on the same `item` in parallel, then a judge picks the best. `Agent[i]` outputs `candidates[i]`, judge selects `winner`.

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    item         │ │    item         │ │    item         │
│  output/        │ │  output/        │ │  output/        │
│    candidates[0]│ │    candidates[1]│ │    candidates[2]│
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌───────────────┐
                    │     Judge     │
                    └───────┬───────┘
                            │
                            ▼
                         winner
```

```python
# Signature
await swarm.best_of(
    item=FileMap | SwarmResult,
    prompt=str,
    config=BestOfConfig(                    # n?, judge_criteria, task_agents?, judge_agent?, callbacks
        judge_criteria='...',
        n=3,
        on_candidate_complete=lambda idx, cand_idx, status: ...,
        on_judge_complete=lambda idx, winner_idx, reasoning: ...,
    ),
    name=str,                               # Operation name for observability (appears in meta.operation_name)
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    retry=RetryConfig(...),                 # Per-candidate retry (judge uses default)
    timeout_ms=int,                         # Optional
) -> BestOfResult
```

```python
input_item = {'task.txt': 'Complex problem...'}

result = await swarm.best_of(
    item=input_item,
    prompt='Solve this problem',
    config=BestOfConfig(
        n=3,
        judge_criteria='Most accurate and well-explained solution',
        on_candidate_complete=lambda idx, cand_idx, status: print(f'Candidate {cand_idx}: {status}'),
        on_judge_complete=lambda idx, winner_idx, reasoning: print(f'Winner: {winner_idx}'),
    ),
)

print(result.winner)          # Best SwarmResult
print(result.winner_index)    # 0, 1, or 2
print(result.judge_reasoning) # Why this was chosen
print(result.candidates)      # All candidate results
```

Use different agents per candidate:

```python
claude_agent = AgentConfig(type='claude', model='opus')
codex_agent = AgentConfig(type='codex', model='gpt-5.2-codex')
gemini_agent = AgentConfig(type='gemini', model='gemini-3-flash')

result = await swarm.best_of(
    item=input_item,
    prompt='Solve this',
    config=BestOfConfig(
        task_agents=[claude_agent, codex_agent, gemini_agent],
        judge_criteria='Best solution quality',
        judge_agent=claude_agent,
        mcp_servers={...},           # (optional) MCP servers for candidates
        judge_mcp_servers={...},     # (optional) MCP servers for judge
        skills=['pdf'],              # (optional) Skills for candidates
        judge_skills=['pdf'],        # (optional) Skills for judge
        composio=ComposioSetup(...), # (optional) Composio config for candidates
        judge_composio=ComposioSetup(...),  # (optional) Composio config for judge
    ),
)
```

### 2.2 map

Process items in parallel. `Agent[i]` sees `items[i]` and outputs `results[i]` (which includes `result.json` if `schema` provided).

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    items[0]     │ │    items[1]     │ │    items[2]     │
│  output/        │ │  output/        │ │  output/        │
│    results[0]   │ │    results[1]   │ │    results[2]   │
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              [results[0], results[1], results[2]]
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.map(
    items=list[FileMap] | list[SwarmResult],
    prompt=str | Callable[[FileMap, int], str],
    name=str,                               # Operation name for observability (appears in meta.operation_name)
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    best_of=BestOfConfig,                   # N candidates + judge (mutually exclusive with verify)
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    skills=list[str],                       # Optional - e.g. ['pdf', 'dev-browser']
    composio=ComposioSetup,                 # Composio Tool Router config
    timeout_ms=int,                         # Optional
) -> SwarmResultList
```

```python
# Basic
results = await swarm.map(
    items=documents,
    prompt='Summarize this document',
)
```

When `schema` is provided, a structured output prompt is automatically embedded—instructing the agent to write `output/result.json` matching the schema.

```python
# With Pydantic schema
class SummarySchema(BaseModel):
    title: str
    key_points: list[str]

results = await swarm.map(
    items=documents,
    prompt='Extract summary',
    schema=SummarySchema,
)

# Or with JSON Schema
summary_json_schema = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'key_points': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['title', 'key_points'],
}

results = await swarm.map(
    items=documents,
    prompt='Extract summary',
    schema=summary_json_schema,
)

# With dynamic prompt
results = await swarm.map(
    items=documents,
    prompt=lambda files, index: f'Analyze document {index + 1}: focus on revenue',
)

# Access results
for r in results:
    if r.status == 'success':
        print(r.data)   # Parsed schema instance or FileMap
        print(r.files)  # Output files from agent
```

### 2.3 map with best_of

Combine map parallelism with best_of quality:

```python
class AnalysisSchema(BaseModel):
    findings: list[str]
    confidence: float

# Each item gets N candidates, judge picks best per item
results = await swarm.map(
    items=documents,
    prompt='Analyze thoroughly',
    schema=AnalysisSchema,
    best_of=BestOfConfig(
        n=3,
        judge_criteria='Most comprehensive analysis',
        # task_agents=[...],       # Different agent per candidate
        # judge_agent=...,         # Override judge agent
        # mcp_servers={...},       # MCP servers for candidates
        # judge_mcp_servers={...}, # MCP servers for judge
        # skills=[...],            # Skills for candidates
        # judge_skills=[...],      # Skills for judge
    ),
)

# Results contain only winners (one per input item)
```

### 2.4 filter

Two-step evaluation (`schema` and `condition` are required):
1. `Agent[i]` sees `items[i]`, assesses it, outputs `result.json` matching `schema`
2. SDK parses `result.json` → `data`, your `condition(data)` applies the threshold
3. Passing items forward their original input files, not agent output

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    items[0]     │ │    items[1]     │ │    items[2]     │
│  output/        │ │  output/        │ │  output/        │
│    result.json  │ │    result.json  │ │    result.json  │
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   condition(data)
                      ✓    ✗    ✓
                      │         │
                      ▼         ▼
                [items[0], items[2]]
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.filter(
    items=list[FileMap] | list[SwarmResult],
    prompt=str,                             # Describe what to assess (agent outputs result.json)
    name=str,                               # Operation name for observability (appears in meta.operation_name)
    schema=PydanticModel | dict,            # Required - defines evaluation output structure
    condition=Callable[[Any], bool],        # Local function applies threshold
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    skills=list[str],                       # Optional - e.g. ['pdf', 'dev-browser']
    composio=ComposioSetup,                 # Composio Tool Router config
    timeout_ms=int,                         # Optional
) -> SwarmResultList
```

```python
class EvalSchema(BaseModel):
    severity: Literal['critical', 'warning', 'info']
    score: float

results = await swarm.filter(
    items=documents,
    prompt='Assess the severity of issues in this document',  # Agent evaluates
    schema=EvalSchema,
    condition=lambda data: data.severity == 'critical',       # Code applies threshold
)

# Three possible statuses:
results.success    # Passed condition
results.filtered   # Evaluated but didn't pass
results.error      # Agent error

# Chain to next step
await swarm.reduce(
    items=results.success,
    prompt='Summarize critical issues',
)
```

### 2.5 reduce

Synthesize many items into one. A single agent sees all `items` as `item_0/`, `item_1/`, etc. and outputs a unified `result` (which includes `result.json` if `schema` provided).

```
        ┌─────────────────────────┐
        │         Sandbox         │
        │         Agent           │
        │                         │
        │  context/               │
        │    item_0/items[0]      │
        │    item_1/items[1]      │
        │    item_2/items[2]      │
        │  output/                │
        │    result               │
        └────────────┬────────────┘
                     │
                     ▼
                  result
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.reduce(
    items=list[FileMap] | list[SwarmResult],
    prompt=str,
    name=str,                               # Operation name for observability (appears in meta.operation_name)
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    skills=list[str],                       # Optional - e.g. ['pdf', 'dev-browser']
    composio=ComposioSetup,                 # Composio Tool Router config
    timeout_ms=int,                         # Optional
) -> ReduceResult
```

```python
# Agent sees: item_0/, item_1/, item_2/, etc.
report = await swarm.reduce(
    items=results.success,
    prompt='Create a unified report from all analyses',
)

if report.status == 'success':
    print(report.files)  # Final output files
    print(report.data)   # Parsed schema if provided

# With schema
class ReportSchema(BaseModel):
    summary: str
    recommendations: list[str]

report = await swarm.reduce(
    items=items,
    prompt='Create report',
    schema=ReportSchema,
)
```

## 3. Result Types

```python
@dataclass
class SwarmResult:
    """Result from map, filter, best_of candidates."""
    status: Literal['success', 'filtered', 'error']
    data: Any | None        # Parsed schema, or None on error
    files: FileMap          # Output files (map/best_of) or input files (filter)
    meta: IndexedMeta       # operation_id, operation, tag, sandbox_id, item_index
    error: str | None       # Error message if status == 'error'
    raw_data: str | None    # Raw result.json when parse/validation failed
    best_of: BestOfInfo | None  # Present when map used best_of option
    verify: VerifyInfo | None   # Present when verify option was used

# SwarmResultList - from map, filter (extends list)
results.success    # list[SwarmResult] with status 'success'
results.filtered   # list[SwarmResult] with status 'filtered'
results.error      # list[SwarmResult] with status 'error'

@dataclass
class ReduceResult:
    """Result from reduce."""
    status: Literal['success', 'error']
    data: Any | None
    files: FileMap
    meta: ReduceMeta        # operation_id, operation, tag, sandbox_id, input_count, input_indices
    error: str | None
    raw_data: str | None
    verify: VerifyInfo | None

@dataclass
class VerifyInfo:
    """Verification outcome."""
    passed: bool            # Final verification status
    reasoning: str          # Verifier's reasoning
    verify_meta: VerifyMeta # operation_id, operation, tag, sandbox_id, attempts
    attempts: int           # Total attempts made

@dataclass
class BestOfInfo:
    """Present when map used best_of option."""
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta   # operation_id, operation, tag, sandbox_id, candidate_count
    candidates: list[SwarmResult]

@dataclass
class BestOfResult:
    """Result from best_of."""
    winner: SwarmResult
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta   # operation_id, operation, tag, sandbox_id, candidate_count
    candidates: list[SwarmResult]
```

## 4. Chaining Operations

When chaining Swarm operations, `result.json` from a previous step is automatically renamed to `data.json`. This avoids confusion when the downstream agent writes its own `result.json`. This also applies to [Pipeline](#7-pipeline).

**Example: map → reduce chain**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MAP (parallel)                                                             │
│                                                                             │
│  item_0 agent writes:          item_1 agent writes:                         │
│  output/                       output/                                      │
│    result.json ← schema        result.json ← schema                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  REDUCE (single agent)                                                      │
│                                                                             │
│  context/                                                                   │
│    item_0/                                                                  │
│      data.json      ← renamed from result.json                              │
│    item_1/                                                                  │
│      data.json      ← renamed from result.json                              │
│  output/                                                                    │
│    result.json      ← reduce agent writes its own                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
class AnalysisSchema(BaseModel):
    summary: str

class SeveritySchema(BaseModel):
    severity: Literal['critical', 'warning', 'info']

# Full pipeline: map → filter → reduce
analyzed = await swarm.map(
    items=documents,
    prompt='Analyze',
    schema=AnalysisSchema,
)

critical = await swarm.filter(
    items=analyzed.success,
    prompt='Evaluate severity',
    schema=SeveritySchema,
    condition=lambda d: d.severity == 'critical',
)

report = await swarm.reduce(
    items=critical.success,
    prompt='Create summary report',
)

# Combine success and filtered
all_evaluated = [*critical.success, *critical.filtered]
await swarm.reduce(
    items=all_evaluated,
    prompt='Summarize all evaluated items',
)
```

## 5. AgentOverride

Override the default agent for any operation (api_key inherited from Swarm config):

```python
@dataclass
class AgentConfig:
    type: Literal['claude', 'codex', 'gemini', 'qwen']
    api_key: str | None = None
    model: str | None = None
    reasoning_effort: Literal['low', 'medium', 'high', 'xhigh'] | None = None  # Codex only
    betas: list[str] | None = None  # Claude only
```

```python
codex_agent = AgentConfig(
    type='codex',
    reasoning_effort='high',
)

results = await swarm.map(
    items=items,
    prompt='Analyze',
    agent=codex_agent,
)
```

## 6. Concurrency

Global semaphore limits parallel sandboxes across all operations.

```python
swarm = Swarm(SwarmConfig(
    agent=agent,
    concurrency=4,  # Max 4 sandboxes at once (default: 4)
))

# map(10) with best_of(5) = 60 agent calls, but only 4 run at any time
```

**Ordering guarantees:**
- `best_of`: Judge runs only after all candidates complete
- `map` → `filter` → `reduce`: Each phase completes before next starts
- Within a phase: Items run in parallel (up to concurrency limit)

---

## 7. Pipeline

Fluent wrapper over Swarm for chaining operations. **All Swarm features work in Pipeline steps** — `schema`, `best_of`, `verify`, `retry`, `agent`, `mcp_servers`, `skills`, `composio`, dynamic prompts.

```python
from dotenv import load_dotenv
load_dotenv()

from swarmkit import Swarm, Pipeline

swarm = Swarm()  # See Swarm Abstractions for full config

pipeline = (
    Pipeline(swarm)
    .map(MapConfig(
        name='analyze',
        prompt='Analyze...',
        schema=AnalysisSchema,
    ))
    .filter(FilterConfig(
        name='critical',
        prompt='Rate...',
        schema=SeveritySchema,
        condition=lambda d: d.severity == 'critical',
    ))
    .reduce(ReduceConfig(
        name='report',
        prompt='Summarize...',
    ))
)

# Reusable — run with different data
result1 = await pipeline.run(batch1)
result2 = await pipeline.run(batch2)
```

### Step Configurations

Each step accepts the same options as the corresponding Swarm method, plus `name` for observability:

```python
# Map step — same as swarm.map() + name
MapConfig(
    name=str,                               # Step name (appears in events)
    prompt=str | Callable[[FileMap, int], str],
    schema=PydanticModel | dict,            # Optional
    best_of=BestOfConfig,                   # N candidates + judge
    verify=VerifyConfig,                    # LLM-as-judge quality check
    retry=RetryConfig,                      # Auto-retry on error
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    skills=list[str],                       # Skills for workers
    composio=ComposioSetup,                 # Composio Tool Router config
    system_prompt=str,
    timeout_ms=int,
)

# Filter step — same as swarm.filter() + name + emit
FilterConfig(
    name=str,
    prompt=str,
    schema=PydanticModel | dict,            # Required
    condition=Callable[[Any], bool],        # Required
    emit='success' | 'filtered' | 'all',    # What passes to next step (default: 'success')
    verify=VerifyConfig,
    retry=RetryConfig,
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    skills=list[str],                       # Skills for workers
    composio=ComposioSetup,                 # Composio Tool Router config
    system_prompt=str,
    timeout_ms=int,
)

# Reduce step — same as swarm.reduce() + name (terminal: no steps after)
ReduceConfig(
    name=str,
    prompt=str,
    schema=PydanticModel | dict,            # Optional
    verify=VerifyConfig,
    retry=RetryConfig,
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    skills=list[str],                       # Skills for workers
    composio=ComposioSetup,                 # Composio Tool Router config
    system_prompt=str,
    timeout_ms=int,
)
```

### Full Example

```python
pipeline = (
    Pipeline(swarm)

    .map(MapConfig(
        name='analyze',
        prompt=lambda files, idx: f'Analyze document {idx + 1}',
        schema=AnalysisSchema,
        best_of=BestOfConfig(
            n=3,
            judge_criteria='Most thorough analysis',
        ),
        retry=RetryConfig(max_attempts=2),
        agent=AgentConfig(type='claude', model='opus'),
    ))

    .filter(FilterConfig(
        name='quality-gate',
        prompt='Rate the analysis quality',
        schema=QualitySchema,  # Has score: float, reasoning: str
        condition=lambda d: d.score >= 8,
        emit='success',                     # Only high-quality pass through
        verify=VerifyConfig(
            criteria='Rating must be justified with specific examples',
        ),
    ))

    .reduce(ReduceConfig(
        name='synthesize',
        prompt='Create executive summary from all analyses',
        schema=ReportSchema,
        verify=VerifyConfig(
            criteria='Summary must cover all key findings',
        ),
    ))

    .on('step_complete', lambda e: print(f'{e.name}: {e.success_count}/{e.success_count + e.error_count}'))
)

result = await pipeline.run(documents)
```

### Events

Pipeline unifies all Swarm callbacks at the pipeline level, adding `step_index` and `step_name`:

```python
(
    pipeline
    .on('step_start', lambda e: print(f'Step {e.index} started with {e.item_count} items'))
    .on('step_complete', lambda e: print(f'Step {e.index} done in {e.duration_ms}ms'))
    .on('step_error', lambda e: print(f'Step {e.index} failed: {e.error}'))
)

# Or object style
pipeline.on(PipelineEvents(
    on_step_complete=lambda e: print(f'{e.name}: {e.success_count} success'),
    on_item_retry=lambda e: print(f'Retry: step {e.step_index}, item {e.item_index}'),
    on_verifier_complete=lambda e: print(f"Verify: {'PASS' if e.passed else e.feedback}"),
))
```

| Event | Fields |
|-------|--------|
| `step_start` | `type`, `index`, `name?`, `item_count` |
| `step_complete` | `type`, `index`, `name?`, `duration_ms`, `success_count`, `error_count`, `filtered_count` |
| `step_error` | `type`, `index`, `name?`, `error` |
| `item_retry` | `step_index`, `step_name?`, `item_index`, `attempt`, `error` |
| `worker_complete` | `step_index`, `step_name?`, `item_index`, `attempt`, `status` |
| `verifier_complete` | `step_index`, `step_name?`, `item_index`, `attempt`, `passed`, `feedback?` |
| `candidate_complete` | `step_index`, `step_name?`, `item_index`, `candidate_index`, `status` |
| `judge_complete` | `step_index`, `step_name?`, `item_index`, `winner_index`, `reasoning` |

### Result

```python
@dataclass
class PipelineResult:
    pipeline_run_id: str
    steps: list[StepResult]   # type, index, duration_ms, results
    output: list[SwarmResult] | ReduceResult
    total_duration_ms: int

# Access step results
for step in result.steps:
    print(f'{step.type} took {step.duration_ms}ms')
```

### Terminal Pipeline

After `.reduce()`, no more steps can be added (returns `TerminalPipeline`):

```python
terminal = pipeline.reduce(ReduceConfig(prompt='...'))
terminal.map(MapConfig(prompt='...'))  # Raises: "Cannot add steps after reduce"
```

---
