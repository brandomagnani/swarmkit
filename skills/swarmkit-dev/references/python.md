# Python SDK Reference

## Table of Contents
- [Installation](#installation)
- [SwarmKit](#swarmkit)
- [Skills](#skills)
- [Composio](#composio)
- [Swarm](#swarm)
- [Pipeline](#pipeline)
- [Types](#types)

> **Note:** Requires Node.js 18+ (SDK uses a lightweight Node.js bridge).

---

## Installation

```bash
pip install swarmkit
```

## SwarmKit

### Basic Setup

```python
from swarmkit import SwarmKit, AgentConfig, ComposioSetup, ComposioConfig

swarmkit = SwarmKit(
    config=AgentConfig(type='claude'),
    skills=['pdf', 'dev-browser'],
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['github', 'gmail']),
    ),
)

await swarmkit.run(prompt='Analyze this document')
output = await swarmkit.get_output_files()
await swarmkit.kill()
```

### Full Configuration

```python
import os
from pydantic import BaseModel
from swarmkit import SwarmKit, AgentConfig, E2BProvider, ComposioSetup, ComposioConfig

class ResultSchema(BaseModel):
    summary: str
    score: float

sandbox = E2BProvider(
    api_key=os.getenv('E2B_API_KEY'),
    timeout_ms=3600000,
)

swarmkit = SwarmKit(
    config=AgentConfig(
        type='codex',
        model='gpt-5.2-codex',
        reasoning_effort='high',
        api_key=os.getenv('SWARMKIT_API_KEY'),
    ),
    sandbox=sandbox,
    context={'docs/readme.txt': 'Context content...'},
    files={'scripts/setup.sh': '#!/bin/bash\necho hello'},
    system_prompt='You are a careful pair programmer.',
    schema=ResultSchema,
    skills=['pdf', 'docx'],
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(
            toolkits=['github', 'gmail'],
            tools={'github': ['github_create_issue']},
            keys={'stripe': 'sk_live_...'},
        ),
    ),
    mcp_servers={
        'local': {'command': 'npx', 'args': ['-y', 'some-mcp'], 'env': {'API_KEY': '...'}},
        'remote': {'type': 'http', 'url': 'https://...', 'headers': {'x-api-key': '...'}},
    },
    secrets={'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN')},
    session_tag_prefix='my-app',
)
```

### Runtime Methods

```python
# Run agent
result = await swarmkit.run(
    prompt='Analyze the data',
    timeout_ms=15 * 60 * 1000,
    background=False,
)

# Execute shell command
cmd_result = await swarmkit.execute_command(
    command='pytest',
    timeout_ms=10 * 60 * 1000,
)

# Get output files
output = await swarmkit.get_output_files(recursive=True)
print(output.files)   # dict
print(output.data)    # Pydantic model instance or None
print(output.error)   # Validation error or None

# Upload files
await swarmkit.upload_context({'spec.json': json.dumps(data)})
await swarmkit.upload_files({'scripts/run.sh': '#!/bin/bash\necho hi'})

# Session management
session_id = await swarmkit.get_session()
await swarmkit.pause()
await swarmkit.resume()
await swarmkit.set_session('existing-sandbox-id')
await swarmkit.kill()

# Constructor param for reconnection
swarmkit2 = SwarmKit(
    config=AgentConfig(type='claude'),
    sandbox_id='existing-sandbox-id',  # Reconnect on next run()
)

# Port forwarding
url = await swarmkit.get_host(8000)
```

### Context Manager

```python
async with swarmkit:
    result = await swarmkit.run(prompt='...')
    output = await swarmkit.get_output_files()
# Automatically calls kill()
```

### Streaming

```python
swarmkit.on('stdout', lambda data: print(data, end=''))
swarmkit.on('stderr', lambda data: print(f'[ERR] {data}', end=''))
swarmkit.on('content', lambda event: print(event['update']))
```

**Events:**

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
| `tool_call` | Tool started | `toolCallId`, `title`, `kind`, `status`, `rawInput?` |
| `tool_call_update` | Tool finished | `toolCallId`, `status?`, `title?`, `content?` |
| `plan` | TodoWrite updates | `entries[]` with `content`, `status`, `priority` |

**Key patterns:**
- `tool_call` (start) and `tool_call_update` (end) share `toolCallId`
- `tool_call_update` may arrive before `tool_call` (handle out-of-order)
- Flush messages before rendering tools/plan (preserves interleaving)
- `kind` values: `read`, `edit`, `search`, `execute`, `think`, `fetch`, `switch_mode`, `other`

### Composio Static Methods

```python
# Get OAuth URL for "Connect GitHub" button
result = await SwarmKit.composio.auth('user_123', 'github')
# result.url → render as <a href={result.url}>Connect GitHub</a>

# Check connection status (all toolkits)
status = await SwarmKit.composio.status('user_123')
# {'github': True, 'gmail': False, 'slack': True}

# Check single toolkit
is_connected = await SwarmKit.composio.status('user_123', 'github')
# True | False

# Get detailed connection info
connections = await SwarmKit.composio.connections('user_123')
# [ComposioConnectionStatus(toolkit='github', connected=True, account_id='ca_...'), ...]
```

### Helper Functions

```python
from swarmkit import read_local_dir, save_local_dir

# Read local directory → FileMap (for upload)
files = read_local_dir('./input', recursive=True)
await swarmkit.upload_context(files)

# Save FileMap → local directory (for download)
output = await swarmkit.get_output_files(recursive=True)
save_local_dir('./output', output.files)
```

### Observability

```python
swarmkit = SwarmKit(
    config=AgentConfig(type='claude'),
    session_tag_prefix='my-project',
)

await swarmkit.run(prompt='...')

print(await swarmkit.get_session_tag())        # "my-project-ab12cd34"
print(await swarmkit.get_session_timestamp())  # ISO timestamp for log file
```

Log files: `~/.swarmkit/observability/sessions/{tag}_{provider}_{sandboxId}_{agent}_{timestamp}.jsonl`

---

## Skills

Skills extend agent capabilities with specialized tools and workflows.

```python
swarmkit = SwarmKit(
    skills=['pdf', 'dev-browser'],
)
```

[Browse all available skills](https://github.com/brandomagnani/swarmkit/tree/main/skills)

---

## Composio

Access 1000+ integrations (GitHub, Gmail, Slack, etc.) via [Composio](https://composio.dev).

- [Tool Router Overview](https://docs.composio.dev/tool-router/overview)
- [Available Toolkits](https://docs.composio.dev/toolkits/introduction)

```python
swarmkit = SwarmKit(
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['github', 'gmail']),
    ),
)
```

---

## Swarm

### Basic Setup

```python
from swarmkit import Swarm, SwarmConfig, AgentConfig, RetryConfig, ComposioSetup, ComposioConfig

swarm = Swarm(SwarmConfig(
    agent=AgentConfig(type='claude'),
    skills=['pdf'],
    composio=ComposioSetup(
        user_id='user_123',
        config=ComposioConfig(toolkits=['github']),
    ),
    concurrency=4,
    timeout_ms=3_600_000,
    tag='my-pipeline',
    retry=RetryConfig(max_attempts=3, backoff_ms=1000, backoff_multiplier=2),
))
```

### Operation Signatures

```python
# map - parallel processing with optional quality options
await swarm.map(
    items,                    # list[FileMap] | list[SwarmResult]
    prompt,                   # str | Callable[[FileMap, int], str]
    schema=None,              # Pydantic model or JSON Schema dict
    agent=None, best_of=None, verify=None, retry=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None
) # → list[SwarmResult]

# filter - gate with condition (schema & condition required)
await swarm.filter(
    items, prompt,
    schema,                   # Required
    condition,                # Callable[[Any], bool] - Required
    agent=None, verify=None, retry=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None
    # Note: best_of NOT available
) # → SwarmResultList with .success, .filtered, .error

# reduce - synthesize many → one
await swarm.reduce(
    items, prompt, schema=None,
    agent=None, verify=None, retry=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None
    # Note: best_of NOT available
) # → ReduceResult

# best_of - N candidates, judge picks winner
await swarm.best_of(
    item,                     # FileMap | SwarmResult (single item)
    prompt, config,           # BestOfConfig with judge_criteria
    schema=None, agent=None, retry=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None
) # → BestOfResult
```

### map

```python
from pydantic import BaseModel

class SummarySchema(BaseModel):
    title: str
    key_points: list[str]

results = await swarm.map(
    items=[
        {'report.txt': 'Q1 revenue...'},
        {'report.txt': 'Q2 revenue...'},
    ],
    prompt='Summarize this document',
    schema=SummarySchema,
    agent=AgentConfig(type='claude', model='opus'),
    skills=['pdf'],
    retry=RetryConfig(max_attempts=2),
)

for r in results:
    if r.status == 'success':
        print(r.data)   # SummarySchema instance
        print(r.files)  # Output files
```

### map with best_of

```python
from swarmkit import BestOfConfig

results = await swarm.map(
    items=documents,
    prompt='Analyze thoroughly',
    schema=AnalysisSchema,
    best_of=BestOfConfig(
        n=3,
        judge_criteria='Most comprehensive analysis',
        task_agents=[
            AgentConfig(type='claude', model='opus'),
            AgentConfig(type='codex', model='gpt-5.2-codex'),
            AgentConfig(type='gemini'),
        ],
        judge_agent=AgentConfig(type='claude'),
    ),
)
```

### map with verify

```python
from swarmkit import VerifyConfig

results = await swarm.map(
    items=documents,
    prompt='Extract data',
    schema=DataSchema,
    verify=VerifyConfig(
        criteria='All required fields must be present and accurate',
        max_attempts=3,
        verifier_agent=AgentConfig(type='claude', model='opus'),
    ),
)
```

### filter

```python
from typing import Literal

class EvalSchema(BaseModel):
    severity: Literal['critical', 'warning', 'info']
    score: float

results = await swarm.filter(
    items=documents,
    prompt='Assess the severity of issues',
    schema=EvalSchema,
    condition=lambda data: data.severity == 'critical',
)

print(results.success)   # Passed condition
print(results.filtered)  # Didn't pass
print(results.error)     # Errors
```

### reduce

```python
class ReportSchema(BaseModel):
    summary: str
    recommendations: list[str]

report = await swarm.reduce(
    items=results.success,
    prompt='Create a unified report from all analyses',
    schema=ReportSchema,
)

if report.status == 'success':
    print(report.data)
```

### best_of

```python
result = await swarm.best_of(
    item={'task.txt': 'Complex problem...'},
    prompt='Solve this problem',
    config=BestOfConfig(
        n=3,
        judge_criteria='Most accurate solution',
        on_candidate_complete=lambda idx, cand_idx, status: print(f'Candidate {cand_idx}: {status}'),
        on_judge_complete=lambda idx, winner_idx, reasoning: print(f'Winner: {winner_idx}'),
    ),
)

print(result.winner)
print(result.winner_index)
print(result.judge_reasoning)
```

---

## Pipeline

### Step Config Signatures

```python
# MapConfig - same options as swarm.map() + name
MapConfig(name=None, prompt, schema=None, best_of=None, verify=None, retry=None, agent=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None)

# FilterConfig - same options as swarm.filter() + name + emit
FilterConfig(name=None, prompt, schema, condition, emit=None, verify=None, retry=None, agent=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None)
# emit: 'success' | 'filtered' | 'all' (default: 'success')

# ReduceConfig - same options as swarm.reduce() + name (terminal step)
ReduceConfig(name=None, prompt, schema=None, verify=None, retry=None, agent=None, skills=None, composio=None, mcp_servers=None, system_prompt=None, timeout_ms=None)
```

```python
from swarmkit import Swarm, Pipeline, MapConfig, FilterConfig, ReduceConfig, BestOfConfig, VerifyConfig, RetryConfig

swarm = Swarm()

pipeline = (
    Pipeline(swarm)
    .map(MapConfig(
        name='analyze',
        prompt=lambda files, idx: f'Analyze document {idx + 1}',
        schema=AnalysisSchema,
        best_of=BestOfConfig(n=3, judge_criteria='Most thorough'),
    ))
    .filter(FilterConfig(
        name='quality-gate',
        prompt='Rate the analysis quality',
        schema=QualitySchema,
        condition=lambda d: d.score >= 8,
        emit='success',
    ))
    .reduce(ReduceConfig(
        name='synthesize',
        prompt='Create executive summary',
        schema=ReportSchema,
    ))
    .on('step_start', lambda e: print(f'Step {e.index} started'))
    .on('step_complete', lambda e: print(f'Step {e.index} done'))
)

result = await pipeline.run(documents)
print(result.output)
```

### Pipeline Events

```python
(
    pipeline
    .on('step_start', lambda e: print(f'Step {e.index}: {e.item_count} items'))
    .on('step_complete', lambda e: print(f'Step {e.index}: {e.success_count} success in {e.duration_ms}ms'))
    .on('step_error', lambda e: print(f'Step {e.index} failed: {e.error}'))
    .on('item_retry', lambda e: print(f'Retry: step {e.step_index}, item {e.item_index}'))
    .on('candidate_complete', lambda e: print(f'Candidate {e.candidate_index}: {e.status}'))
    .on('judge_complete', lambda e: print(f'Winner: {e.winner_index}'))
    .on('verifier_complete', lambda e: print(f"Verify: {'PASS' if e.passed else e.feedback}"))
)
```

| Event | Fields |
|-------|--------|
| `step_start` | `index`, `name?`, `item_count` |
| `step_complete` | `index`, `name?`, `duration_ms`, `success_count`, `error_count`, `filtered_count` |
| `step_error` | `index`, `name?`, `error` |
| `item_retry` | `step_index`, `step_name?`, `item_index`, `attempt`, `error` |
| `candidate_complete` | `step_index`, `step_name?`, `item_index`, `candidate_index`, `status` |
| `judge_complete` | `step_index`, `step_name?`, `item_index`, `winner_index`, `reasoning` |
| `verifier_complete` | `step_index`, `step_name?`, `item_index`, `attempt`, `passed`, `feedback?` |

---

## Types

### AgentConfig

```python
@dataclass
class AgentConfig:
    type: Literal['claude', 'codex', 'gemini', 'qwen'] = 'claude'
    api_key: str | None = None
    provider_api_key: str | None = None
    oauth_token: str | None = None
    model: str | None = None
    reasoning_effort: Literal['low', 'medium', 'high', 'xhigh'] | None = None  # Codex only
    betas: list[str] | None = None  # Claude only
```

### ComposioSetup

```python
@dataclass
class ComposioSetup:
    user_id: str
    config: ComposioConfig | None = None

@dataclass
class ComposioConfig:
    toolkits: list[str] | None = None
    tools: dict[str, ToolsFilter] | None = None
    keys: dict[str, str] | None = None
    auth_configs: dict[str, str] | None = None

ToolsFilter = Union[
    list[str],
    dict[Literal['enable'], list[str]],
    dict[Literal['disable'], list[str]],
    dict[Literal['tags'], list[str]],
]
```

### RetryConfig

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_ms: int = 1000
    backoff_multiplier: float = 2
    retry_on: Callable[[SwarmResult], bool] | None = None
    on_item_retry: Callable[[int, int, str], None] | None = None
```

### McpServerConfig

```python
# STDIO: command present → local subprocess
# HTTP:  url + type: "http" → remote server
# SSE:   url without type → remote (default)
McpServerConfig = {
    'type': str,                                      # "stdio" | "http" | "sse"
    'command': str, 'args': list, 'cwd': str,         # STDIO
    'url': str, 'headers': dict[str, str],            # HTTP/SSE
    'env': dict[str, str],                            # Common
}
```

### BestOfConfig

```python
@dataclass
class BestOfConfig:
    judge_criteria: str
    n: int = 3
    task_agents: list[AgentConfig] | None = None
    judge_agent: AgentConfig | None = None
    skills: list[str] | None = None
    judge_skills: list[str] | None = None
    composio: ComposioSetup | None = None
    judge_composio: ComposioSetup | None = None
    mcp_servers: dict[str, McpServerConfig] | None = None
    judge_mcp_servers: dict[str, McpServerConfig] | None = None
    on_candidate_complete: Callable[[int, int, str], None] | None = None
    on_judge_complete: Callable[[int, int, str], None] | None = None
```

### VerifyConfig

```python
@dataclass
class VerifyConfig:
    criteria: str
    max_attempts: int = 3
    verifier_agent: AgentConfig | None = None
    verifier_skills: list[str] | None = None
    verifier_composio: ComposioSetup | None = None
    verifier_mcp_servers: dict[str, McpServerConfig] | None = None
    on_worker_complete: Callable[[int, int, str], None] | None = None
    on_verifier_complete: Callable[[int, int, bool, str | None], None] | None = None
```

### SwarmResult

```python
@dataclass
class SwarmResult:
    status: Literal['success', 'filtered', 'error']
    data: Any | None
    files: dict[str, bytes]
    meta: IndexedMeta
    error: str | None = None
    raw_data: str | None = None
    best_of: BestOfInfo | None = None
    verify: VerifyInfo | None = None
```

### AgentResponse

```python
@dataclass
class AgentResponse:
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
```

### OutputResult

```python
@dataclass
class OutputResult:
    files: dict[str, bytes]
    data: Any | None
    error: str | None = None
    raw_data: str | None = None
```

### ReduceResult

```python
@dataclass
class ReduceResult:
    status: Literal['success', 'error']
    data: Any | None
    files: dict[str, bytes]
    meta: ReduceMeta
    error: str | None = None
    raw_data: str | None = None
    verify: VerifyInfo | None = None
```

### BestOfResult

```python
@dataclass
class BestOfResult:
    winner: SwarmResult
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta
    candidates: list[SwarmResult]
```

### SwarmConfig

```python
@dataclass
class SwarmConfig:
    agent: AgentConfig | None = None
    skills: list[str] | None = None
    composio: ComposioSetup | None = None
    mcp_servers: dict[str, McpServerConfig] | None = None
    concurrency: int = 4
    timeout_ms: int = 3_600_000
    tag: str = 'swarm'
    retry: RetryConfig | None = None
```

### PipelineResult

```python
@dataclass
class PipelineResult:
    pipeline_run_id: str
    steps: list[StepResult]   # type, index, duration_ms, results
    output: list[SwarmResult] | ReduceResult
    total_duration_ms: int
```

### Meta Types

```python
@dataclass
class IndexedMeta:
    operation_id: str
    operation: str
    tag: str
    sandbox_id: str
    item_index: int

@dataclass
class ReduceMeta:
    operation_id: str
    operation: str
    tag: str
    sandbox_id: str
    input_count: int
    input_indices: list[int]

@dataclass
class JudgeMeta:
    operation_id: str
    operation: str
    tag: str
    sandbox_id: str
    candidate_count: int

@dataclass
class VerifyMeta:
    operation_id: str
    operation: str
    tag: str
    sandbox_id: str
    attempts: int

@dataclass
class BestOfInfo:
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta
    candidates: list[SwarmResult]

@dataclass
class VerifyInfo:
    passed: bool
    reasoning: str
    verify_meta: VerifyMeta
    attempts: int
```
