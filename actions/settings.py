# -*- coding: utf-8 -*-
"""Settings action — configuration overview for Stablecoin Payment Gateway."""

from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich import box

from pipeline.ui import console, print_info, print_warning


def action_settings():
    """Display setup instructions: config.json sections and examples."""
    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="bright_green",
        box=box.ROUNDED,
        title="[bold bright_green] ◈ CONFIGURATION ◈ [/]",
        title_style="bright_green",
    )
    table.add_column("Setting", style="bright_green")
    table.add_column("Description", style="dim")
    table.add_column("Example", style="bright_black")

    table.add_row('merchant.pay_to_address', 'Payout wallet (non-custodial)', '0xYourWalletAddress')
    table.add_row('merchant.xpub', 'xpub for address derivation', 'xpub6C...')
    table.add_row('invoice.ttl_minutes', 'Invoice expiry window', '30')
    table.add_row('invoice.confirmations', 'Per-chain confirmation floors', '"polygon": 64')
    table.add_row('chains.<name>.rpc', 'RPC endpoint per network', 'https://mainnet.base.org')
    table.add_row('tokens', 'Accepted stablecoins', '"USDC": {"enabled": true}')
    table.add_row('x402.facilitator_url', 'Verification/settlement service', 'https://x402.org/facilitator')
    table.add_row('webhooks.secret', 'HMAC webhook signing secret', '"whsec_..."')
    table.add_row('server.port', 'Gateway listen port', '8080')

    panel = Panel(
        table,
        title="[bold bright_green] Stablecoin Payment Gateway Settings [/]",
        border_style="bright_green",
        box=box.DOUBLE,
    )

    console.print()
    console.print(panel)

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config.json"

    console.print()
    console.print("[dim]Configuration files:[/]")
    console.print(f"  [bright_green]config.json[/]  → {config_path}")
    console.print()
    print_info('The gateway never touches your keys — addresses derive from the xpub.')
    print_info('For production mainnet settlement, point x402.facilitator_url at your own facilitator.')
    print_warning("Keep API keys and secrets secure. Never commit config.json to version control.")
    print_info("Edit config files with any text editor (e.g. VS Code, Notepad).")
