---
name: agent-browser
description: CLI-based headless browser automation for AI agents. Use when users ask to automate web browsing via command-line, interact with web pages using accessibility snapshots, scrape websites, fill forms, take screenshots, or perform browser testing. Ideal for simple sequential browser tasks. Trigger phrases include "use agent-browser", "browse to", "automate this website", "get page snapshot", "click element", "fill form field". Prefer this over dev-browser for simpler tasks that don't need complex Playwright scripting.
---

# Agent Browser

CLI tool for browser automation via bash commands. Uses snapshot + ref workflow optimized for AI agents.

## Setup (Run First)

Run setup script before first use:

```bash
skills/agent-browser/scripts/setup.sh
```

After setup, run all commands from the skill directory:

```bash
cd skills/agent-browser && npx agent-browser <command>
```

## Core Workflow

1. Navigate to URL
2. Get accessibility snapshot with element refs
3. Interact using refs (`@e1`, `@e2`, etc.)
4. Repeat snapshot after page changes

```bash
cd skills/agent-browser && npx agent-browser open example.com
cd skills/agent-browser && npx agent-browser snapshot -i --json
cd skills/agent-browser && npx agent-browser click @e2
cd skills/agent-browser && npx agent-browser fill @e3 "text"
cd skills/agent-browser && npx agent-browser snapshot -i --json
cd skills/agent-browser && npx agent-browser close
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

> All commands below assume you're in the skill directory or prefix with `cd skills/agent-browser &&`

### Navigation
```bash
npx agent-browser open <url>
npx agent-browser back
npx agent-browser forward
npx agent-browser reload
npx agent-browser close
```

### Interaction
```bash
npx agent-browser click <sel>              # Click element
npx agent-browser dblclick <sel>           # Double-click element
npx agent-browser fill <sel> <text>        # Clear and fill input
npx agent-browser type <sel> <text>        # Type without clearing
npx agent-browser press <key>              # Press key (Enter, Tab, Control+a)
npx agent-browser hover <sel>              # Hover element
npx agent-browser focus <sel>              # Focus element
npx agent-browser check <sel>              # Check checkbox
npx agent-browser uncheck <sel>            # Uncheck checkbox
npx agent-browser select <sel> <value>     # Select dropdown option
npx agent-browser scroll up|down [px]      # Scroll page
npx agent-browser scrollintoview <sel>     # Scroll element into view
npx agent-browser drag <src> <tgt>         # Drag and drop
npx agent-browser upload <sel> <files>     # Upload files
```

### Getting Data
```bash
npx agent-browser get text <sel>           # Get text content
npx agent-browser get html <sel>           # Get innerHTML
npx agent-browser get value <sel>          # Get input value
npx agent-browser get attr <sel> <attr>    # Get attribute
npx agent-browser get title                # Page title
npx agent-browser get url                  # Current URL
npx agent-browser get count <sel>          # Count matching elements
npx agent-browser get box <sel>            # Get bounding box
```

### State Checks
```bash
npx agent-browser is visible <sel>
npx agent-browser is enabled <sel>
npx agent-browser is checked <sel>
```

### Screenshots & PDF
```bash
npx agent-browser screenshot output.png    # Save screenshot to file
npx agent-browser screenshot --full pg.png # Full page screenshot
npx agent-browser pdf output.pdf           # Save as PDF
```

### Wait
```bash
npx agent-browser wait <selector>          # Wait for element
npx agent-browser wait <ms>                # Wait for time
npx agent-browser wait --text "Welcome"    # Wait for text
npx agent-browser wait --url "**/dash"     # Wait for URL pattern
npx agent-browser wait --load networkidle  # Wait for load state
npx agent-browser wait --fn "window.ready" # Wait for JS condition
```

## Selectors

### Refs (Preferred)
Use refs from snapshot output:
```bash
npx agent-browser click @e2
npx agent-browser fill @e3 "email@test.com"
```

### CSS Selectors
```bash
npx agent-browser click "#submit"
npx agent-browser click ".btn-primary"
npx agent-browser click "div > button"
```

### Text & XPath
```bash
npx agent-browser click "text=Submit"
npx agent-browser click "xpath=//button"
```

### Semantic Locators
```bash
npx agent-browser find role button click --name "Submit"
npx agent-browser find label "Email" fill "test@test.com"
npx agent-browser find text "Sign In" click
npx agent-browser find placeholder "Search" fill "query"
```

## Sessions

Run isolated browser instances:
```bash
npx agent-browser --session agent1 open site-a.com
npx agent-browser --session agent2 open site-b.com

# Or via environment
AGENT_BROWSER_SESSION=agent1 npx agent-browser click @e2

# List sessions
npx agent-browser session list
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
cd skills/agent-browser
npx agent-browser open https://example.com/login
npx agent-browser snapshot -i --json
npx agent-browser fill @e1 "username"
npx agent-browser fill @e2 "password"
npx agent-browser click @e3  # Submit button
npx agent-browser wait --url "**/dashboard"
npx agent-browser snapshot -i --json
```

### Form Submission
```bash
cd skills/agent-browser
npx agent-browser open https://example.com/form
npx agent-browser snapshot -i --json
npx agent-browser fill @e1 "John Doe"
npx agent-browser fill @e2 "john@example.com"
npx agent-browser select @e3 "Option A"
npx agent-browser check @e4
npx agent-browser click @e5  # Submit
npx agent-browser wait --text "Success"
```

### Data Extraction
```bash
cd skills/agent-browser
npx agent-browser open https://example.com/data
npx agent-browser snapshot --json > page_structure.json
npx agent-browser get text ".results" --json
npx agent-browser screenshot results.png
```

## Debugging

```bash
cd skills/agent-browser
npx agent-browser --headed open example.com  # See browser window
npx agent-browser screenshot debug.png        # Capture current state
npx agent-browser highlight <sel>             # Highlight element visually
npx agent-browser console                     # View console messages
npx agent-browser errors                      # View page errors
npx agent-browser trace start                 # Start trace recording
# ... do actions ...
npx agent-browser trace stop trace.zip        # Save trace
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
