/**
 * Cookbook UI helpers (prompt + output renderer).
 *
 * Goal: keep `factotum.ts` minimal. It should need only:
 * - `readPrompt()` for user input
 * - `makeRenderer()` for streaming content output
 */

import chalk from "chalk";
import logUpdate from "log-update";
import { marked } from "marked";
import { markedTerminal } from "marked-terminal";
import boxen from "boxen";
import readline from "node:readline";

// Configure marked for terminal output
marked.use(markedTerminal() as marked.MarkedExtension);

// ─────────────────────────────────────────────────────────────
// Theme colors (matching Python Rich theme)
// ─────────────────────────────────────────────────────────────

const theme = {
  info: chalk.cyan,
  warning: chalk.magenta,
  error: chalk.bold.red,
  success: chalk.bold.green,
  muted: chalk.dim.white,
  thought: chalk.dim.italic,
  tool: chalk.dim.cyan,
};

// Spinner frames (matching Rich "dots" spinner)
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

// ─────────────────────────────────────────────────────────────
// Console helpers
// ─────────────────────────────────────────────────────────────

export const console_ = {
  print: (msg: string = "") => console.log(msg),
  printSuccess: (msg: string) => console.log(theme.success(msg)),
  printMuted: (msg: string) => console.log(theme.muted(msg)),
  printInfo: (msg: string) => console.log(theme.info(msg)),
};

// ─────────────────────────────────────────────────────────────
// Prompt input
// ─────────────────────────────────────────────────────────────

export async function readPrompt(): Promise<string> {
  // Ensure any previous live block is finalized.
  logUpdate.clear();
  logUpdate.done();

  const bgHex = "#303030";
  const prefixColor = "#00d75f";

  const bg = chalk.bgHex(bgHex);
  const promptPrefix = bg(chalk.hex(prefixColor).bold("> "));
  const indentPrefix = bg("  ");

  const width = process.stdout.columns || 100;
  // Don't hard-cap input height: grow to show full prompt.
  // (If the prompt exceeds terminal height, the terminal will necessarily scroll.)
  const maxInputLines = Number.POSITIVE_INFINITY;

  const buffer: string[] = [];
  let escArmed = false;
  let isPasting = false;

  function wrapVisualLines(text: string): string[] {
    const lines = text.split(/\r?\n/);
    const visual: string[] = [];
    const availFirst = Math.max(1, width - 2);
    const avail = availFirst;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] ?? "";
      if (line.length === 0) {
        visual.push("");
        continue;
      }
      for (let j = 0; j < line.length; j += avail) {
        visual.push(line.slice(j, j + avail));
      }
    }
    return visual;
  }

  function consumeBracketedPaste(input: string): string {
    // Terminals in bracketed paste mode wrap paste with:
    //   ESC [ 200 ~  ...paste...  ESC [ 201 ~
    // We'll strip markers and toggle isPasting.
    const start = "\u001b[200~";
    const end = "\u001b[201~";
    let out = input;

    // Process multiple markers if present.
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const s = out.indexOf(start);
      const e = out.indexOf(end);
      if (s === -1 && e === -1) break;
      if (s !== -1 && (e === -1 || s < e)) {
        isPasting = true;
        out = out.replace(start, "");
        continue;
      }
      if (e !== -1) {
        isPasting = false;
        out = out.replace(end, "");
      }
    }
    return out;
  }

  function render() {
    const text = buffer.join("");
    const visual = wrapVisualLines(text);

    const out: string[] = [];
    out.push(bg(" ".repeat(width))); // pad above

    for (let i = 0; i < visual.length && i < maxInputLines; i++) {
      const chunk = visual[i] ?? "";
      const prefix = i === 0 ? promptPrefix : indentPrefix;
      const content = bg(chalk.white(chunk));
      const padLen = Math.max(0, width - 2 - chunk.length);
      out.push(prefix + content + bg(" ".repeat(padLen)));
    }

    out.push(bg(" ".repeat(width))); // pad below
    logUpdate(out.join("\n"));
  }

  function printSubmittedPrompt(prompt: string) {
    const lines = prompt.split(/\r?\n/);
    for (const line of lines) {
      const chunks = line.length > width
        ? line.match(new RegExp(`.{1,${width}}`, "g")) ?? [line]
        : [line];
      for (const chunk of chunks) {
        const padLen = Math.max(0, width - chunk.length);
        // No '>' after submit (match python).
        // Full-width background on every physical line.
        console.log(bg(chunk + " ".repeat(padLen)));
      }
    }
  }

  return await new Promise<string>((resolve) => {
    const stdin = process.stdin;
    const wasRaw = (stdin as any).isRaw;

    readline.emitKeypressEvents(stdin);
    if (stdin.isTTY) stdin.setRawMode(true);
    stdin.resume();

    // Enable bracketed paste mode to reliably detect paste boundaries and avoid
    // treating pasted newlines as submit.
    if (process.stdout.isTTY) {
      process.stdout.write("\u001b[?2004h");
    }

    render();

    const cleanup = () => {
      try {
        logUpdate.clear();
        logUpdate.done();
      } catch {
        // ignore
      }
      try {
        if (process.stdout.isTTY) process.stdout.write("\u001b[?2004l");
      } catch {
        // ignore
      }
      try {
        if (stdin.isTTY) stdin.setRawMode(Boolean(wasRaw));
      } catch {
        // ignore
      }
      try {
        stdin.pause();
      } catch {
        // ignore
      }
    };

    const onKeypress = (str: string, key: any) => {
      try {
        const safeStr = typeof str === "string" ? str : "";
        str = consumeBracketedPaste(safeStr);

        if (key?.ctrl && key?.name === "c") {
          cleanup();
          process.exit(0);
        }

        if (key?.name === "escape") {
          escArmed = true;
          return;
        }

        if (key?.name === "return" || key?.name === "enter") {
          // If the newline came from a paste, treat it as input, not submit.
          if (isPasting) {
            buffer.push("\n");
            escArmed = false;
            render();
            return;
          }
          if (escArmed) {
            buffer.push("\n");
            escArmed = false;
            render();
            return;
          }

          // Submit.
          stdin.off("keypress", onKeypress);
          cleanup();

          const value = buffer.join("").replace(/\r/g, "").replace(/\n$/, "");
          buffer.length = 0;

          if (value.length > 0) {
            printSubmittedPrompt(value);
            console.log(); // spacer
          }

          resolve(value);
          return;
        }

        if (key?.name === "backspace") {
          escArmed = false;
          if (buffer.length > 0) {
            const last = buffer[buffer.length - 1] ?? "";
            if (last.length <= 1) buffer.pop();
            else buffer[buffer.length - 1] = last.slice(0, -1);
          }
          render();
          return;
        }

        // Ignore arrows and other control keys.
        if (key?.name && ["up", "down", "left", "right", "home", "end", "pageup", "pagedown"].includes(key.name)) {
          escArmed = false;
          return;
        }

        if (typeof str === "string" && str.length > 0) {
          // Paste may come in as a long string; keep it.
          // Normalize CRLF and keep embedded newlines as text.
          buffer.push(str.replace(/\r/g, ""));
          escArmed = false;
          render();
        }
      } catch {
        // Fail safe: restore terminal state and resolve empty prompt.
        stdin.off("keypress", onKeypress);
        cleanup();
        resolve("");
      }
    };

    stdin.on("keypress", onKeypress);
  });
}

// ─────────────────────────────────────────────────────────────
// Renderer
// ─────────────────────────────────────────────────────────────

interface ToolInfo {
  title: string;
  kind: string;
  status: string;
  rawInput: Record<string, unknown>;
}

interface PlanEntry {
  status: string;
  content: string;
}

const KIND_LABELS: Record<string, string> = {
  read: "Read",
  edit: "Write",
  execute: "Bash",
  fetch: "Fetch",
  search: "Search",
  think: "Task",
  switch_mode: "Mode",
};

export class Renderer {
  private currentMessage = "";
  private thoughtBuffer = "";
  private tools: Map<string, ToolInfo> = new Map();
  private toolOrder: string[] = [];
  private showReasoning: boolean;
  private isLive = false;
  private spinnerFrame = 0;
  private spinnerInterval: ReturnType<typeof setInterval> | null = null;
  private lastPlanStr = "";
  private hasContent = false;
  private lastPrintWasBlank = false;

  constructor(showReasoning = false) {
    this.showReasoning = showReasoning;
  }

  private oneLine(value: unknown, maxLen = 120): string {
    const str = String(value ?? "");
    const compact = str.split(/\s+/).join(" ");
    if (compact.length > maxLen) {
      return compact.slice(0, maxLen - 3) + "...";
    }
    return compact;
  }

  reset(): void {
    this.stopLiveInternal(false);
    this.currentMessage = "";
    this.thoughtBuffer = "";
    this.tools.clear();
    this.toolOrder = [];
    this.lastPlanStr = "";
    this.hasContent = false;
    this.lastPrintWasBlank = false;
  }

  handleEvent(event: { update?: Record<string, unknown> }): void {
    const update = event.update ?? {};
    const eventType = update.sessionUpdate as string | undefined;

    if (eventType === "agent_message_chunk") {
      this.handleMessage(update);
    } else if (eventType === "agent_thought_chunk") {
      this.handleThought(update);
    } else if (eventType === "tool_call") {
      this.handleToolCall(update);
    } else if (eventType === "tool_call_update") {
      this.handleToolUpdate(update);
    } else if (eventType === "plan") {
      this.handlePlan(update);
    }
  }

  private handleMessage(update: Record<string, unknown>): void {
    const content = update.content as Record<string, unknown> | undefined;
    if (content?.type === "text") {
      this.currentMessage += (content.text as string) ?? "";
    }
  }

  private handleThought(update: Record<string, unknown>): void {
    const content = update.content as Record<string, unknown> | undefined;
    if (content?.type === "text") {
      this.thoughtBuffer += (content.text as string) ?? "";
    }
  }

  private handleToolCall(update: Record<string, unknown>): void {
    const toolId = (update.toolCallId as string) ?? "";
    const title = (update.title as string) ?? "Tool";
    const kind = (update.kind as string) ?? "other";
    const rawInput = (update.rawInput as Record<string, unknown>) ?? {};
    const status = (update.status as string) ?? "pending";

    // Flush message first
    this.flushMessage();

    // Upsert tool
    if (!this.tools.has(toolId)) {
      this.toolOrder.push(toolId);
    }
    this.tools.set(toolId, { title, kind, status, rawInput });

    // Skip todo tools (don't refresh for them)
    if (this.shouldSkipTool(title)) {
      return;
    }

    this.refreshLive();
  }

  private handleToolUpdate(update: Record<string, unknown>): void {
    const toolId = (update.toolCallId as string) ?? "";
    const status = update.status as string | undefined;
    const title = update.title as string | undefined;

    // Create placeholder if updates arrive out of order
    if (!this.tools.has(toolId)) {
      this.toolOrder.push(toolId);
      this.tools.set(toolId, {
        title: title ?? "Tool",
        kind: "other",
        status: status ?? "pending",
        rawInput: {},
      });
    }

    const tool = this.tools.get(toolId)!;
    if (status !== undefined && tool.status !== status) {
      tool.status = status;
    }
    if (title) {
      tool.title = title;
    }

    if (this.shouldSkipTool(tool.title)) {
      return;
    }

    this.refreshLive();
  }

  private handlePlan(update: Record<string, unknown>): void {
    const entries = (update.entries as PlanEntry[]) ?? [];
    if (entries.length === 0) return;

    // Flush any buffered message
    this.flushMessage();

    const lines: string[] = [];
    for (const entry of entries) {
      const status = entry.status ?? "pending";
      const content = entry.content ?? "";
      const icon = { completed: "✓", in_progress: "→", pending: "○" }[status] ?? "○";
      lines.push(`${icon} ${content}`);
    }

    const planStr = lines.join("\n");
    if (planStr === this.lastPlanStr) return;
    this.lastPlanStr = planStr;

    // Style the plan
    const styledLines: string[] = [];
    for (const entry of entries) {
      const status = entry.status ?? "pending";
      const content = entry.content ?? "";
      const icon = { completed: "✓", in_progress: "→", pending: "○" }[status] ?? "○";
      const style = {
        completed: theme.success,
        in_progress: theme.info,
        pending: theme.muted,
      }[status] ?? theme.muted;
      styledLines.push(style(`${icon} ${content}`));
    }

    // Clear live area, print plan, restart live
    this.clearLive();

    console.log(
      boxen(styledLines.join("\n"), {
        title: chalk.bold("Plan"),
        titleAlignment: "center",
        borderColor: "cyan",
        padding: { top: 0, bottom: 0, left: 1, right: 1 },
        width: process.stdout.columns ? Math.min(process.stdout.columns - 2, 100) : 100,
      })
    );
    this.lastPrintWasBlank = false;
    console.log();
    this.lastPrintWasBlank = true;
    this.hasContent = true;

    // Restart live area
    this.startLiveInternal();
  }

  private shouldSkipTool(title: string): boolean {
    return (
      title === "write_todos" ||
      title === "TodoWrite" ||
      title.toLowerCase().includes("todo")
    );
  }

  private hasVisibleTools(): boolean {
    for (const toolId of this.toolOrder) {
      const tool = this.tools.get(toolId);
      if (tool && !this.shouldSkipTool(tool.title)) {
        return true;
      }
    }
    return false;
  }

  private formatToolLine(toolId: string): string {
    const tool = this.tools.get(toolId)!;
    const { title, kind, status, rawInput } = tool;

    const content = this.getToolContent(kind, rawInput, title);

    const dotColor =
      status === "completed"
        ? theme.success
        : status === "failed"
        ? theme.error
        : theme.tool;

    const label = KIND_LABELS[kind];
    if (label) {
      return `${dotColor("●")} ${chalk.white(label)}(${theme.muted(this.oneLine(content))})`;
    }
    return `${dotColor("●")} ${chalk.white(title)}(${theme.muted(this.oneLine(content))})`;
  }

  private flushMessage(): void {
    if (this.currentMessage.trim()) {
      // Clear live area
      this.clearLive();

      if (this.hasVisibleTools() && !this.lastPrintWasBlank) {
        console.log();
        this.lastPrintWasBlank = true;
      }

      // Render markdown
      const rendered = marked(this.currentMessage) as string;
      console.log(rendered.trim());
      this.lastPrintWasBlank = false;
      console.log();
      this.lastPrintWasBlank = true;
      this.currentMessage = "";
      this.hasContent = true;

      // Restart live area
      this.startLiveInternal();
    }
  }

  private getToolContent(
    kind: string,
    rawInput: Record<string, unknown>,
    title: string
  ): string {
    if (kind === "fetch") {
      return (rawInput.url as string) ?? (rawInput.query as string) ?? title;
    } else if (kind === "search") {
      return (
        (rawInput.query as string) ??
        (rawInput.pattern as string) ??
        (rawInput.path as string) ??
        title
      );
    } else if (kind === "edit") {
      return (rawInput.file_path as string) ?? (rawInput.path as string) ?? title;
    } else if (kind === "read") {
      return (
        (rawInput.file_path as string) ??
        (rawInput.absolute_path as string) ??
        (rawInput.path as string) ??
        title
      );
    } else if (kind === "execute") {
      return (rawInput.command as string) ?? title;
    } else {
      return (
        (rawInput.command as string) ??
        (rawInput.query as string) ??
        (rawInput.file_path as string) ??
        (rawInput.path as string) ??
        (rawInput.instruction as string) ??
        title
      );
    }
  }

  private renderToolLines(): string[] {
    const lines: string[] = [];
    for (const toolId of this.toolOrder) {
      const tool = this.tools.get(toolId);
      if (!tool || this.shouldSkipTool(tool.title)) continue;
      lines.push(this.formatToolLine(toolId));
    }
    return lines;
  }

  private renderLive(showSpinner: boolean): string {
    const lines = this.renderToolLines();

    if (showSpinner) {
      const frame = SPINNER_FRAMES[this.spinnerFrame % SPINNER_FRAMES.length];
      const spinnerLine = `${theme.info(frame)} ${theme.muted("Working...")}`;

      if (lines.length > 0) {
        lines.push(""); // blank line before spinner
        lines.push(spinnerLine);
      } else {
        lines.push(spinnerLine);
      }
    }

    return lines.join("\n");
  }

  private startLiveInternal(): void {
    if (this.isLive) return;
    this.isLive = true;

    // Start spinner animation
    this.spinnerInterval = setInterval(() => {
      this.spinnerFrame++;
      this.refreshLive();
    }, 80);

    this.refreshLive();
  }

  private refreshLive(): void {
    if (!this.isLive) return;
    logUpdate(this.renderLive(true));
  }

  private clearLive(): void {
    if (!this.isLive) return;

    if (this.spinnerInterval) {
      clearInterval(this.spinnerInterval);
      this.spinnerInterval = null;
    }

    logUpdate.clear();
    this.isLive = false;
  }

  private stopLiveInternal(final: boolean): void {
    if (!this.isLive) return;

    if (this.spinnerInterval) {
      clearInterval(this.spinnerInterval);
      this.spinnerInterval = null;
    }

    logUpdate.clear();
    this.isLive = false;

    if (final) {
      // Print final tool state (without spinner)
      const lines = this.renderToolLines();
      if (lines.length > 0) {
        console.log(lines.join("\n"));
      }
    }
  }

  startLive(): void {
    console.log();
    console.log(chalk.bold.cyan("Factotum"));
    console.log();
    this.lastPrintWasBlank = true;
    this.startLiveInternal();
  }

  stopLive(): void {
    this.stopLiveInternal(true);

    if (this.currentMessage.trim()) {
      if (this.hasVisibleTools()) {
        console.log();
        this.lastPrintWasBlank = true;
      }
      const rendered = marked(this.currentMessage) as string;
      console.log(rendered.trim());
      this.lastPrintWasBlank = false;
    }

    if (this.showReasoning && this.thoughtBuffer.trim()) {
      console.log();
      console.log(
        boxen(theme.thought(this.thoughtBuffer), {
          title: theme.muted("Reasoning"),
          borderColor: "gray",
          padding: { top: 0, bottom: 0, left: 1, right: 1 },
        })
      );
    }
  }
}

// ─────────────────────────────────────────────────────────────
// Factory
// ─────────────────────────────────────────────────────────────

export function makeRenderer(options: { showReasoning?: boolean } = {}): Renderer {
  return new Renderer(options.showReasoning ?? false);
}

// ─────────────────────────────────────────────────────────────
// Panel helper (for welcome message)
// ─────────────────────────────────────────────────────────────

export function printPanel(content: string, options: { borderColor?: string } = {}): void {
  console.log(
    boxen(content, {
      borderColor: options.borderColor ?? "cyan",
      padding: { top: 0, bottom: 0, left: 1, right: 1 },
    })
  );
}
