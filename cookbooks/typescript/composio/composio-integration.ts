/**
 * Composio Integration for SwarmKit
 *
 * Handles Composio Tool Router setup, authentication, and MCP configuration.
 */
import { Composio } from "@composio/core";
import chalk from "chalk";
import { createInterface } from "readline";

export interface ComposioConfig {
  userId: string;
  toolkits?: string[];
  apiKey?: string;
}

export interface McpConfig {
  type: "http";
  url: string;
  headers: Record<string, string>;
}

interface Toolkit {
  name: string;
  slug: string;
  connection: {
    is_active: boolean;
  };
}

export class ComposioIntegration {
  private userId: string;
  private toolkits?: string[];
  private client: Composio;
  private session: any = null;

  constructor(config: ComposioConfig) {
    this.userId = config.userId;
    this.toolkits = config.toolkits;
    const apiKey = config.apiKey || process.env.COMPOSIO_API_KEY;
    this.client = new Composio({ apiKey });
  }

  async createSession() {
    this.session = await this.client.create(this.userId, {
      toolkits: this.toolkits,
    });
    return this.session;
  }

  async getPendingConnections(): Promise<Toolkit[]> {
    if (!this.session) {
      await this.createSession();
    }

    const toolkits = await this.session.toolkits();
    return toolkits.items.filter((t: Toolkit) => !t.connection.is_active);
  }

  async getMcpConfig(): Promise<McpConfig> {
    if (!this.session) {
      await this.createSession();
    }

    return {
      type: "http",
      url: this.session.mcp.url,
      headers: this.session.mcp.headers,
    };
  }

  async authorize(toolkit: string): Promise<string> {
    if (!this.session) {
      await this.createSession();
    }

    const req = await this.session.authorize(toolkit);
    return req.redirect_url;
  }

  async setupWithPreauth(interactive: boolean = true): Promise<McpConfig> {
    console.log(chalk.bold.cyan("\nSetting up Composio integrations...\n"));

    await this.createSession();
    const pending = await this.getPendingConnections();

    if (pending.length > 0) {
      console.log(chalk.yellow("These services need authentication:\n"));
      for (const toolkit of pending) {
        console.log(`  - ${toolkit.name}`);
      }
      console.log();

      if (interactive) {
        const rl = createInterface({
          input: process.stdin,
          output: process.stdout,
        });

        const confirm = await new Promise<boolean>((resolve) => {
          rl.question("Connect them now? [Y/n] ", (answer) => {
            resolve(answer.toLowerCase() !== "n");
          });
        });

        if (confirm) {
          for (const toolkit of pending) {
            const url = await this.authorize(toolkit.slug);
            console.log(chalk.cyan(`\n${toolkit.name}:`), url);
            await new Promise<void>((resolve) => {
              rl.question(chalk.dim("Press Enter after authenticating..."), () => {
                resolve();
              });
            });
          }
          console.log(chalk.green("\nAll services connected!\n"));
        } else {
          console.log(chalk.dim("Skipping. Agent will prompt when needed.\n"));
        }

        rl.close();
      }
    } else {
      console.log(chalk.green("All services already connected!\n"));
    }

    return this.getMcpConfig();
  }
}

export async function setupComposio(
  config: ComposioConfig,
  interactive: boolean = true
): Promise<McpConfig> {
  const integration = new ComposioIntegration(config);
  return integration.setupWithPreauth(interactive);
}
