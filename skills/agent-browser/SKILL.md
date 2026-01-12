---
name: agent-browser
description: CLI-based headless browser automation for AI agents. Use when users ask to automate web browsing via command-line, interact with web pages using accessibility snapshots, scrape websites, fill forms, take screenshots, or perform browser testing. Ideal for simple sequential browser tasks. Trigger phrases include "use agent-browser", "browse to", "automate this website", "get page snapshot", "click element", "fill form field". Prefer this over dev-browser for simpler tasks that don't need complex Playwright scripting.
---

# Agent Browser

CLI tool for browser automation via bash commands. Uses snapshot + ref workflow optimized for AI agents.

## Setup (Run First)

Run setup script before first use:

```bash
~/.swarmkit/skills/agent-browser/scripts/setup.sh
```

After setup, use the full path for all commands:
```bash
~/.local/bin/agent-browser <command>
```

## Core Workflow

1. Navigate to URL
2. Get accessibility snapshot with element refs
3. Interact using refs (`@e1`, `@e2`, etc.)
4. Repeat snapshot after page changes

```bash
~/.local/bin/~/.local/bin/agent-browser open example.com
~/.local/bin/agent-browser snapshot -i --json   # Get interactive elements with refs
~/.local/bin/agent-browser click @e2            # Click by ref
~/.local/bin/agent-browser fill @e3 "text"      # Fill input by ref
~/.local/bin/agent-browser snapshot -i --json   # Get updated state
~/.local/bin/agent-browser close
```

## Snapshot Options

| Flag | Effect |
|------|--------|
| `-i, --interactive` | Only interactive elements (buttons, links, inputs) |
| `-c, --compact` | Remove empty structural elements |
| `-d N, --depth N` | Limit tree depth |
| `-s SEL, --selector SEL` | Scope to CSS selector |
| `--json` | Machine-readable output |

Example output:
```
- heading "Example Domain" [ref=e1] [level=1]
- button "Submit" [ref=e2]
- textbox "Email" [ref=e3]
- link "Learn more" [ref=e4]
```

## Essential Commands

### Navigation
```bash
~/.local/bin/agent-browser open <url>
~/.local/bin/agent-browser back
~/.local/bin/agent-browser forward
~/.local/bin/agent-browser reload
~/.local/bin/agent-browser close
```

### Interaction
```bash
~/.local/bin/agent-browser click <sel>              # Click element
~/.local/bin/agent-browser dblclick <sel>           # Double-click element
~/.local/bin/agent-browser fill <sel> <text>        # Clear and fill input
~/.local/bin/agent-browser type <sel> <text>        # Type without clearing
~/.local/bin/agent-browser press <key>              # Press key (Enter, Tab, Control+a)
~/.local/bin/agent-browser hover <sel>              # Hover element
~/.local/bin/agent-browser focus <sel>              # Focus element
~/.local/bin/agent-browser check <sel>              # Check checkbox
~/.local/bin/agent-browser uncheck <sel>            # Uncheck checkbox
~/.local/bin/agent-browser select <sel> <value>     # Select dropdown option
~/.local/bin/agent-browser scroll up|down [px]      # Scroll page
~/.local/bin/agent-browser scrollintoview <sel>     # Scroll element into view
~/.local/bin/agent-browser drag <src> <tgt>         # Drag and drop
~/.local/bin/agent-browser upload <sel> <files>     # Upload files
```

### Getting Data
```bash
~/.local/bin/agent-browser get text <sel>           # Get text content
~/.local/bin/agent-browser get html <sel>           # Get innerHTML
~/.local/bin/agent-browser get value <sel>          # Get input value
~/.local/bin/agent-browser get attr <sel> <attr>    # Get attribute
~/.local/bin/agent-browser get title                # Page title
~/.local/bin/agent-browser get url                  # Current URL
~/.local/bin/agent-browser get count <sel>          # Count matching elements
~/.local/bin/agent-browser get box <sel>            # Get bounding box
```

### State Checks
```bash
~/.local/bin/agent-browser is visible <sel>
~/.local/bin/agent-browser is enabled <sel>
~/.local/bin/agent-browser is checked <sel>
```

### Screenshots & PDF
```bash
~/.local/bin/agent-browser screenshot output.png    # Save screenshot to file
~/.local/bin/agent-browser screenshot --full pg.png # Full page screenshot
~/.local/bin/agent-browser pdf output.pdf           # Save as PDF
```

### Wait
```bash
~/.local/bin/agent-browser wait <selector>          # Wait for element
~/.local/bin/agent-browser wait <ms>                # Wait for time
~/.local/bin/agent-browser wait --text "Welcome"    # Wait for text
~/.local/bin/agent-browser wait --url "**/dash"     # Wait for URL pattern
~/.local/bin/agent-browser wait --load networkidle  # Wait for load state
~/.local/bin/agent-browser wait --fn "window.ready" # Wait for JS condition
```

## Selectors

### Refs (Preferred)
Use refs from snapshot output:
```bash
~/.local/bin/agent-browser click @e2
~/.local/bin/agent-browser fill @e3 "email@test.com"
```

### CSS Selectors
```bash
~/.local/bin/agent-browser click "#submit"
~/.local/bin/agent-browser click ".btn-primary"
~/.local/bin/agent-browser click "div > button"
```

### Text & XPath
```bash
~/.local/bin/agent-browser click "text=Submit"
~/.local/bin/agent-browser click "xpath=//button"
```

### Semantic Locators
```bash
~/.local/bin/agent-browser find role button click --name "Submit"
~/.local/bin/agent-browser find label "Email" fill "test@test.com"
~/.local/bin/agent-browser find text "Sign In" click
~/.local/bin/agent-browser find placeholder "Search" fill "query"
```

## Sessions

Run isolated browser instances:
```bash
~/.local/bin/agent-browser --session agent1 open site-a.com
~/.local/bin/agent-browser --session agent2 open site-b.com

# Or via environment
AGENT_BROWSER_SESSION=agent1 ~/.local/bin/agent-browser click @e2

# List sessions
~/.local/bin/agent-browser session list
```

## Global Options

| Option | Effect |
|--------|--------|
| `--session <name>` | Use isolated session |
| `--json` | JSON output for parsing |
| `--headed` | Show browser window |
| `--debug` | Debug output |

## Common Patterns

### Login Flow
```bash
~/.local/bin/agent-browser open https://example.com/login
~/.local/bin/agent-browser snapshot -i --json
~/.local/bin/agent-browser fill @e1 "username"
~/.local/bin/agent-browser fill @e2 "password"
~/.local/bin/agent-browser click @e3  # Submit button
~/.local/bin/agent-browser wait --url "**/dashboard"
~/.local/bin/agent-browser snapshot -i --json
```

### Form Submission
```bash
~/.local/bin/agent-browser open https://example.com/form
~/.local/bin/agent-browser snapshot -i --json
~/.local/bin/agent-browser fill @e1 "John Doe"
~/.local/bin/agent-browser fill @e2 "john@example.com"
~/.local/bin/agent-browser select @e3 "Option A"
~/.local/bin/agent-browser check @e4
~/.local/bin/agent-browser click @e5  # Submit
~/.local/bin/agent-browser wait --text "Success"
```

### Data Extraction
```bash
~/.local/bin/agent-browser open https://example.com/data
~/.local/bin/agent-browser snapshot --json > page_structure.json
~/.local/bin/agent-browser get text ".results" --json
~/.local/bin/agent-browser screenshot results.png
```

## Debugging

```bash
~/.local/bin/agent-browser --headed open example.com  # See browser window
~/.local/bin/agent-browser screenshot debug.png        # Capture current state
~/.local/bin/agent-browser highlight <sel>             # Highlight element visually
~/.local/bin/agent-browser console                     # View console messages
~/.local/bin/agent-browser errors                      # View page errors
~/.local/bin/agent-browser trace start                 # Start trace recording
# ... do actions ...
~/.local/bin/agent-browser trace stop trace.zip        # Save trace
```

## Advanced Commands

See [references/commands.md](references/commands.md) for:
- Screenshots (format, quality, element-specific)
- Video recording (limitations noted)
- Tracing with screenshots/snapshots
- Cookies & storage management
- Network interception
- Tabs & windows
- Frames & dialogs
- Mouse control
- Geolocation & device emulation
