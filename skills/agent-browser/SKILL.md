---
name: agent-browser
description: CLI-based headless browser automation for AI agents. Use when users ask to automate web browsing via command-line, interact with web pages using accessibility snapshots, scrape websites, fill forms, take screenshots, or perform browser testing. Ideal for simple sequential browser tasks. Trigger phrases include "use agent-browser", "browse to", "automate this website", "get page snapshot", "click element", "fill form field". Prefer this over dev-browser for simpler tasks that don't need complex Playwright scripting.
---

# Agent Browser

CLI tool for browser automation via bash commands. Uses snapshot + ref workflow optimized for AI agents.

## Setup (Run First)

Run setup script before first use to install agent-browser and Chromium:

```bash
./skills/agent-browser/scripts/setup.sh
```

This installs:
- `agent-browser` CLI globally via npm
- Chromium browser via Playwright

## Core Workflow

1. Navigate to URL
2. Get accessibility snapshot with element refs
3. Interact using refs (`@e1`, `@e2`, etc.)
4. Repeat snapshot after page changes

```bash
agent-browser open example.com
agent-browser snapshot -i --json   # Get interactive elements with refs
agent-browser click @e2            # Click by ref
agent-browser fill @e3 "text"      # Fill input by ref
agent-browser snapshot -i --json   # Get updated state
agent-browser close
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
agent-browser open <url>
agent-browser back
agent-browser forward
agent-browser reload
agent-browser close
```

### Interaction
```bash
agent-browser click <sel>              # Click element
agent-browser dblclick <sel>           # Double-click element
agent-browser fill <sel> <text>        # Clear and fill input
agent-browser type <sel> <text>        # Type without clearing
agent-browser press <key>              # Press key (Enter, Tab, Control+a)
agent-browser hover <sel>              # Hover element
agent-browser focus <sel>              # Focus element
agent-browser check <sel>              # Check checkbox
agent-browser uncheck <sel>            # Uncheck checkbox
agent-browser select <sel> <value>     # Select dropdown option
agent-browser scroll up|down [px]      # Scroll page
agent-browser scrollintoview <sel>     # Scroll element into view
agent-browser drag <src> <tgt>         # Drag and drop
agent-browser upload <sel> <files>     # Upload files
```

### Getting Data
```bash
agent-browser get text <sel>           # Get text content
agent-browser get html <sel>           # Get innerHTML
agent-browser get value <sel>          # Get input value
agent-browser get attr <sel> <attr>    # Get attribute
agent-browser get title                # Page title
agent-browser get url                  # Current URL
agent-browser get count <sel>          # Count matching elements
agent-browser get box <sel>            # Get bounding box
```

### State Checks
```bash
agent-browser is visible <sel>
agent-browser is enabled <sel>
agent-browser is checked <sel>
```

### Screenshots & PDF
```bash
agent-browser screenshot output.png    # Save screenshot to file
agent-browser screenshot --full pg.png # Full page screenshot
agent-browser pdf output.pdf           # Save as PDF
```

### Wait
```bash
agent-browser wait <selector>          # Wait for element
agent-browser wait <ms>                # Wait for time
agent-browser wait --text "Welcome"    # Wait for text
agent-browser wait --url "**/dash"     # Wait for URL pattern
agent-browser wait --load networkidle  # Wait for load state
agent-browser wait --fn "window.ready" # Wait for JS condition
```

## Selectors

### Refs (Preferred)
Use refs from snapshot output:
```bash
agent-browser click @e2
agent-browser fill @e3 "email@test.com"
```

### CSS Selectors
```bash
agent-browser click "#submit"
agent-browser click ".btn-primary"
agent-browser click "div > button"
```

### Text & XPath
```bash
agent-browser click "text=Submit"
agent-browser click "xpath=//button"
```

### Semantic Locators
```bash
agent-browser find role button click --name "Submit"
agent-browser find label "Email" fill "test@test.com"
agent-browser find text "Sign In" click
agent-browser find placeholder "Search" fill "query"
```

## Sessions

Run isolated browser instances:
```bash
agent-browser --session agent1 open site-a.com
agent-browser --session agent2 open site-b.com

# Or via environment
AGENT_BROWSER_SESSION=agent1 agent-browser click @e2

# List sessions
agent-browser session list
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
agent-browser open https://example.com/login
agent-browser snapshot -i --json
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3  # Submit button
agent-browser wait --url "**/dashboard"
agent-browser snapshot -i --json
```

### Form Submission
```bash
agent-browser open https://example.com/form
agent-browser snapshot -i --json
agent-browser fill @e1 "John Doe"
agent-browser fill @e2 "john@example.com"
agent-browser select @e3 "Option A"
agent-browser check @e4
agent-browser click @e5  # Submit
agent-browser wait --text "Success"
```

### Data Extraction
```bash
agent-browser open https://example.com/data
agent-browser snapshot --json > page_structure.json
agent-browser get text ".results" --json
agent-browser screenshot results.png
```

## Debugging

```bash
agent-browser --headed open example.com  # See browser window
agent-browser screenshot debug.png        # Capture current state
agent-browser highlight <sel>             # Highlight element visually
agent-browser console                     # View console messages
agent-browser errors                      # View page errors
agent-browser trace start                 # Start trace recording
# ... do actions ...
agent-browser trace stop trace.zip        # Save trace
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
