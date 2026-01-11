"""
Composio Integration for SwarmKit

Handles Composio Tool Router setup, authentication, and MCP configuration.
"""
import os
import asyncio
from composio import Composio
from rich.console import Console
from rich.prompt import Confirm

console = Console()


class ComposioIntegration:
    """Manages Composio session and pre-authentication flow."""

    def __init__(
        self,
        user_id: str,
        toolkits: list[str] | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize Composio integration.

        Args:
            user_id: Unique identifier for this user's session
            toolkits: List of toolkits to enable (None = all available)
            api_key: Composio API key (defaults to COMPOSIO_API_KEY env var)
        """
        self.user_id = user_id
        self.toolkits = toolkits
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY")
        self.client = Composio(api_key=self.api_key)
        self.session = None

    def create_session(self):
        """Create Composio session with configured toolkits."""
        self.session = self.client.create(
            user_id=self.user_id,
            toolkits=self.toolkits,
        )
        return self.session

    def get_pending_connections(self) -> list:
        """Get list of toolkits that need authentication."""
        if not self.session:
            self.create_session()

        toolkits = self.session.toolkits()
        return [t for t in toolkits.items if not t.connection.is_active]

    def get_mcp_config(self) -> dict:
        """Get MCP server configuration for SwarmKit."""
        if not self.session:
            self.create_session()

        return {
            "type": "http",
            "url": self.session.mcp.url,
            "headers": self.session.mcp.headers,
        }

    async def authorize(self, toolkit: str) -> str:
        """
        Get authorization URL for a toolkit.

        Returns:
            OAuth redirect URL for user to authenticate
        """
        if not self.session:
            self.create_session()

        req = self.session.authorize(toolkit)
        # API returns redirectUrl (camelCase)
        return getattr(req, "redirectUrl", None) or getattr(req, "redirect_url", None)

    async def setup_with_preauth(self, interactive: bool = True) -> dict:
        """
        Setup Composio with interactive pre-authentication.

        Args:
            interactive: If True, prompts user to authenticate pending services

        Returns:
            MCP server configuration dict
        """
        console.print("\n[bold cyan]Setting up Composio integrations...[/bold cyan]\n")

        self.create_session()
        pending = self.get_pending_connections()

        if pending:
            console.print("[yellow]These services need authentication:[/yellow]\n")
            for toolkit in pending:
                console.print(f"  - {toolkit.name}")
            console.print()

            if interactive and Confirm.ask("Connect them now?", default=True):
                for toolkit in pending:
                    url = await self.authorize(toolkit.slug)
                    console.print(f"\n[cyan]{toolkit.name}:[/cyan] {url}")
                    console.print("[dim]Press Enter after authenticating...[/dim]")
                    await asyncio.to_thread(input)
                console.print("\n[green]All services connected![/green]\n")
            else:
                console.print("[dim]Skipping. Agent will prompt when needed.[/dim]\n")
        else:
            console.print("[green]All services already connected![/green]\n")

        return self.get_mcp_config()


async def setup_composio(
    user_id: str,
    toolkits: list[str] | None = None,
    api_key: str | None = None,
    interactive: bool = True,
) -> dict:
    """
    Convenience function to setup Composio with pre-authentication.

    Args:
        user_id: Unique identifier for this user's session
        toolkits: List of toolkits to enable (None = all available)
        api_key: Composio API key (defaults to COMPOSIO_API_KEY env var)
        interactive: If True, prompts user to authenticate pending services

    Returns:
        MCP server configuration dict for use with SwarmKit

    Example:
        mcp_config = await setup_composio(
            user_id="user-123",
            toolkits=["gmail", "slack", "github"],
        )

        agent = SwarmKit(
            mcp_servers={"composio": mcp_config}
        )
    """
    integration = ComposioIntegration(
        user_id=user_id,
        toolkits=toolkits,
        api_key=api_key,
    )
    return await integration.setup_with_preauth(interactive=interactive)
