<p align="center">
  <img src="assets/swarmkit-logo.png" alt="SwarmKit" height="100">
</p>

<br>

<p align="center">
  Embed autonomous AI agents into any application — in a few lines of code.
</p>

<br>

- Run any CLI agent ([Claude Code](https://github.com/anthropics/claude-code), [Codex](https://github.com/openai/codex), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Qwen Code](https://github.com/QwenLM/qwen-code)) in secure cloud sandboxes
- Persistent filesystem for infinite context
- Full computer access: terminal, browser, MCP tools
- [Agent skills](https://agentskills.io/home): extend agents with custom capabilities (PDF, dev-browser, etc.)
- 500+ integrations (Gmail, GitHub, Slack, Notion & more) via [Composio](https://github.com/ComposioHQ/composio)
- Functional programming abstractions (map, filter, reduce) for massively parallel workloads
- Streaming and structured output
- [Built-in observability](https://dashboard.swarmlink.ai/)
- Much more coming...

## Get Started

### 1. Install the SDK

```bash
npm install @swarmkit/sdk    # TypeScript
pip install swarmkit         # Python
```

**Note:** Requires [Node.js 18+](https://nodejs.org/) (the Python SDK uses a lightweight Node.js bridge).

### 2. Run your first agent

Bring your own keys:
```bash
# .env - Direct (BYOK)
ANTHROPIC_API_KEY=sk-ant-...         # or CLAUDE_CODE_OAUTH_TOKEN (Claude Max), OPENAI_API_KEY, GEMINI_API_KEY
E2B_API_KEY=e2b_...                  # sandbox provider, get at https://e2b.dev
```

Or get your SwarmKit API key at [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai) ([see 3. below](#swarmkit-gateway)):
```bash
# .env - Gateway
SWARMKIT_API_KEY=sk-...
```

Then run:
```typescript
import { SwarmKit } from "@swarmkit/sdk";

const swarmkit = new SwarmKit();  // auto-resolves env variables
await swarmkit.run({ prompt: "Create hello.txt with 'Hello World'" });
const output = await swarmkit.getOutputFiles();  // output.files
```

```python
from swarmkit import SwarmKit

swarmkit = SwarmKit()  # auto-resolves env variables
await swarmkit.run(prompt="Create hello.txt with 'Hello World'")
output = await swarmkit.get_output_files()  # output.files
```

<a id="swarmkit-gateway"></a>

### 3. Unlock full power with SwarmKit API key

Sign up at [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai/) and get your **SwarmKit API key** for:
- Agent execution traces, observability and analytics
- Centralized billing across all providers
- Mix any model with any CLI agent
- $10 FREE CREDITS, no CC required

### 4. Learn more

Check out the [documentation](https://github.com/brandomagnani/swarmkit/tree/main/docs) and [cookbooks](https://github.com/brandomagnani/swarmkit/tree/main/cookbooks).

## Documentation

- [TypeScript SDK](./docs/typescript-sdk.md)
- [Python SDK](./docs/python-sdk.md)
- [Cookbooks](./cookbooks)

## Support + Talk with Founders

- [Community Discord](https://discord.gg/Q36D8dGyNF)
- [Schedule Demo](https://cal.com/brando-magnani/swarmkit-1-1-onboarding-chat)
- Email: [brandomagnani@swarmlink.ai](mailto:brandomagnani@swarmlink.ai)

## Reporting Bugs

We welcome your feedback. File a [GitHub issue](https://github.com/brandomagnani/swarmkit/issues) to report bugs or request features.

## License

See the [LICENSE](./LICENSE) file for full terms and conditions.
