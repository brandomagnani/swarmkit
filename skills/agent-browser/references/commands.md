# Agent Browser Command Reference

Complete reference for all agent-browser commands.

> **Note**: All examples use `agent-browser` for brevity. Use full path `~/.local/bin/agent-browser` after setup.

## Table of Contents

- [Cookies & Storage](#cookies--storage)
- [Network](#network)
- [Tabs & Windows](#tabs--windows)
- [Frames](#frames)
- [Dialogs](#dialogs)
- [Mouse Control](#mouse-control)
- [Keyboard](#keyboard)
- [Browser Settings](#browser-settings)
- [JavaScript Evaluation](#javascript-evaluation)
- [File Operations](#file-operations)
- [Screenshots & Visual Capture](#screenshots--visual-capture)
- [Video Recording](#video-recording)
- [Tracing](#tracing)
- [State Management](#state-management)

---

## Cookies & Storage

### Cookies
```bash
agent-browser cookies                    # Get all cookies
agent-browser cookies set <name> <value> # Set cookie
agent-browser cookies clear              # Clear all cookies
```

### Local Storage
```bash
agent-browser storage local              # Get all localStorage
agent-browser storage local <key>        # Get specific key
agent-browser storage local set <k> <v>  # Set value
agent-browser storage local clear        # Clear all
```

### Session Storage
```bash
agent-browser storage session            # Get all sessionStorage
agent-browser storage session <key>      # Get specific key
agent-browser storage session set <k> <v> # Set value
agent-browser storage session clear      # Clear all
```

---

## Network

### Route Interception
```bash
agent-browser network route <url>              # Intercept requests
agent-browser network route <url> --abort      # Block requests
agent-browser network route <url> --body <json> # Mock response
agent-browser network unroute [url]            # Remove routes
```

### Request Tracking
```bash
agent-browser network requests                 # View tracked requests
agent-browser network requests --filter api    # Filter by pattern
agent-browser network requests --clear         # Clear tracked requests
```

---

## Tabs & Windows

### Tab Management
```bash
agent-browser tab                     # List all tabs
agent-browser tab new [url]           # Open new tab (optionally with URL)
agent-browser tab <n>                 # Switch to tab n (0-indexed)
agent-browser tab close [n]           # Close tab (current if n not specified)
```

### Window Management
```bash
agent-browser window new              # Open new window
```

---

## Frames

```bash
agent-browser frame <selector>        # Switch to iframe by selector
agent-browser frame main              # Switch back to main frame
```

---

## Dialogs

Handle alert/confirm/prompt dialogs:
```bash
agent-browser dialog accept [text]    # Accept dialog (with optional prompt text)
agent-browser dialog dismiss          # Dismiss dialog
```

---

## Mouse Control

```bash
agent-browser mouse move <x> <y>      # Move mouse to coordinates
agent-browser mouse down [button]     # Press mouse button (left/right/middle)
agent-browser mouse up [button]       # Release mouse button
agent-browser mouse wheel <dy> [dx]   # Scroll wheel (dy = vertical, dx = horizontal)
```

### Drag and Drop
```bash
agent-browser drag <source> <target>  # Drag from source to target selector
```

---

## Keyboard

```bash
agent-browser press <key>             # Press and release key
agent-browser keydown <key>           # Hold key down
agent-browser keyup <key>             # Release key
```

### Key Examples
- Single keys: `Enter`, `Tab`, `Escape`, `Backspace`, `Delete`
- Modifiers: `Control+a`, `Shift+Tab`, `Meta+c` (Cmd on Mac)
- Arrow keys: `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`
- Function keys: `F1`, `F2`, etc.

---

## Browser Settings

### Viewport & Device
```bash
agent-browser set viewport <width> <height>  # Set viewport size
agent-browser set device <name>              # Emulate device ("iPhone 14", "iPad Pro")
```

### Geolocation
```bash
agent-browser set geo <latitude> <longitude> # Set geolocation
```

### Network Conditions
```bash
agent-browser set offline on|off      # Toggle offline mode
agent-browser set headers <json>      # Set extra HTTP headers
agent-browser set credentials <u> <p> # Set HTTP basic auth
```

### Media & Appearance
```bash
agent-browser set media dark|light    # Emulate color scheme
```

---

## JavaScript Evaluation

```bash
agent-browser eval <script>           # Run JavaScript and return result
```

Example:
```bash
agent-browser eval "document.querySelectorAll('a').length"
agent-browser eval "window.scrollY"
agent-browser eval "localStorage.getItem('token')"
```

---

## File Operations

### Upload
```bash
agent-browser upload <selector> <file1> [file2...]  # Upload files to input
```

### Download
```bash
agent-browser download <selector> <path>  # Click download link, save to path
```

---

## Screenshots & Visual Capture

### Basic Screenshot
```bash
agent-browser screenshot output.png          # Save to file
agent-browser screenshot --full page.png     # Full scrollable page
```

Always provide a file path - this returns just the path, keeping output minimal.

### Screenshot Options
| Option | Effect |
|--------|--------|
| `--full, -f` | Full page screenshot |
| `--format png\|jpeg` | Image format |
| `--quality <0-100>` | JPEG quality (jpeg only) |
| `--selector <sel>` | Screenshot specific element |

### Element Screenshot
```bash
agent-browser screenshot --selector "#modal" modal.png
agent-browser screenshot --selector "@e5" element.png
```

### PDF Export
```bash
agent-browser pdf output.pdf          # Save page as PDF
```

---

## Video Recording

**Note**: Video recording has limitations - must be enabled at browser launch.

```bash
agent-browser video_start <path>      # Start recording
agent-browser video_stop              # Stop and get video path
```

Current behavior: `video_start` returns a note that video must be enabled with `--video` flag at browser launch. This feature is not fully implemented.

**Alternative**: Use tracing with screenshots for visual debugging.

---

## Tracing

Captures timeline of actions with optional screenshots and DOM snapshots.

### Basic Tracing
```bash
agent-browser trace start             # Start recording
# ... perform actions ...
agent-browser trace stop trace.zip    # Save trace file
```

### Trace Options
```bash
agent-browser trace start --screenshots    # Include screenshots at each step
agent-browser trace start --snapshots      # Include DOM snapshots
```

### Viewing Traces
```bash
npx playwright show-trace trace.zip
```

---

## State Management

### Auth State
```bash
agent-browser state save <path>       # Save cookies/storage to file
agent-browser state load <path>       # Load saved state
```

---

## Semantic Locators (find)

Full syntax for `find` command:

```bash
agent-browser find <type> <value> <action> [actionValue] [options]
```

### Locator Types
| Type | Example |
|------|---------|
| `role` | `find role button click --name "Submit"` |
| `text` | `find text "Sign In" click` |
| `label` | `find label "Email" fill "test@test.com"` |
| `placeholder` | `find placeholder "Search" fill "query"` |
| `alt` | `find alt "Logo" click` |
| `title` | `find title "Close" click` |
| `testid` | `find testid "submit-btn" click` |
| `first` | `find first ".item" click` |
| `last` | `find last ".item" click` |
| `nth` | `find nth 2 "a" click` |

### Actions
- `click` - Click element
- `fill <value>` - Fill input with value
- `check` - Check checkbox
- `hover` - Hover element
- `text` - Get text content

### Options
- `--name <name>` - Filter by accessible name (for role locator)
- `--exact` - Exact text match

---

## Command Options Reference

| Option | Applicable Commands | Effect |
|--------|---------------------|--------|
| `--json` | All | JSON output |
| `--session <name>` | All | Use named session |
| `--headed` | `open`, `launch` | Show browser window |
| `--full, -f` | `screenshot` | Full page screenshot |
| `--name, -n` | `find role` | Filter by name |
| `--exact` | `find text/label` | Exact match |
| `--debug` | All | Debug output |

---

## Response Format

With `--json` flag, all commands return:

### Success
```json
{
  "success": true,
  "data": { ... }
}
```

### Error
```json
{
  "success": false,
  "error": "Error message"
}
```

### Snapshot Response
```json
{
  "success": true,
  "data": {
    "snapshot": "- heading \"Title\" [ref=e1]...",
    "refs": {
      "e1": { "role": "heading", "name": "Title" },
      "e2": { "role": "button", "name": "Submit" }
    }
  }
}
```
