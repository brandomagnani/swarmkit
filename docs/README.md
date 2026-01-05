# SwarmKit

Embed autonomous AI agents into any application — in a few lines of code.

- Secure cloud sandboxes with persistent filesystem
- Agent response streaming
- Structured output
- MCP servers & multi-agent orchestration
- Swarm abstractions for massively parallel workloads
- Built-in observability

Much more coming...

## Documentation

- [TypeScript SDK](../docs/typescript-sdk.md)
- [Python SDK](../docs/python-sdk.md)
- [Cookbooks](../cookbooks)

## Get Started

**1. Install the SDK:**

```bash
npm install @swarmkit/sdk    # TypeScript
pip install swarmkit         # Python
```

**Note:** Requires [Node.js 18+](https://nodejs.org/) (the Python SDK uses a lightweight Node.js bridge).

**2. Run your first agent:**

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...         # or anthropic, or
CLAUDE_CODE_OAUTH_TOKEN=...          # Claude Max subscription, or
OPENAI_API_KEY=sk-...                # Codex / Qwen, or
GEMINI_API_KEY=...                   # Gemini
```

```typescript
import { SwarmKit } from "@swarmkit/sdk";

const swarmkit = new SwarmKit();
await swarmkit.run({ prompt: "Create hello.txt with 'Hello World'" });
const output = await swarmkit.getOutputFiles();  // output.files
```

```python
from swarmkit import SwarmKit

swarmkit = SwarmKit()
await swarmkit.run(prompt="Create hello.txt with 'Hello World'")
output = await swarmkit.get_output_files()  # output.files
```

**3. Unlock full power with SwarmKit API key:**

Sign up at [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai/) and get your **SwarmKit API key** for:
- Agent execution traces, observability and analytics
- Centralized billing across all providers
- Mix any model with any CLI agent
- $10 free credits, no CC required

Then check out the [documentation](https://github.com/brandomagnani/swarmkit/tree/main/docs) and [cookbooks](https://github.com/brandomagnani/swarmkit/tree/main/cookbooks)!

## Support + Talk with Founders

- [Community Discord](https://discord.gg/Q36D8dGyNF)
- [Schedule Demo](https://cal.com/brando-magnani/swarmkit-1-1-onboarding-chat)
- Email: [brandomagnani@swarmlink.ai](mailto:brandomagnani@swarmlink.ai)

## Reporting Bugs

We welcome your feedback. File a [GitHub issue](https://github.com/brandomagnani/swarmkit/issues) to report bugs or request features.

## License

See the [LICENSE](../LICENSE) file for full terms and conditions.
