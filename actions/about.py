# -*- coding: utf-8 -*-
"""About action — project info, features, requirements for Stablecoin Payment Gateway."""

from rich.table import Table
from rich.panel import Panel
from rich import box

from pipeline.ui import console


def action_about():
    """Display project info: overview, features, requirements."""
    features_table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="bright_green",
        box=box.SIMPLE,
        title="[bold bright_green] ◈ FEATURES ◈ [/]",
        title_style="bright_green",
    )
    features_table.add_column("Feature", style="bright_green")
    features_table.add_column("Status", justify="center", style="bright_green")

    for feat in [
        'Self-hosted, non-custodial stablecoin payment gateway',
        'x402 protocol support (HTTP 402 pay-per-request)',
        'Fixed-amount invoices with unique deposit addresses',
        'Shareable payment links with conversion stats',
        'HMAC-SHA256 signed webhooks with retry backoff',
        'USDC / USDT / PYUSD / DAI across 8 networks',
        'Per-chain confirmation policy (12–64 blocks)',
        'xpub-based address derivation — gateway never holds keys',
        'Merchant REST API with scoped, rotatable keys',
        'Settlement monitor with mempool + block watchers',
        'Under/over-payment handling and invoice TTL',
        'Cross-platform (Windows/Linux/macOS), Docker-friendly',
    ]:
        features_table.add_row(feat, "✓")

    setup_table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="bright_green",
        box=box.MINIMAL_HEAVY_HEAD,
        title="[bold bright_green] ◈ REQUIREMENTS & SETUP ◈ [/]",
        title_style="bright_green",
    )
    setup_table.add_column("Item", style="bright_green")
    setup_table.add_column("Note", style="dim")
    setup_table.add_row('Python', '3.10 or higher')
    setup_table.add_row('pip', 'Latest version recommended')
    setup_table.add_row('Libraries', 'rich, cryptography, requests, aiohttp, qrcode')
    setup_table.add_row('Install', 'pip install -r requirements.txt')
    setup_table.add_row('Run', 'python main.py')
    setup_table.add_row('Wallet', 'EVM address or xpub — funds go straight to you')
    setup_table.add_row('Facilitator', 'Public x402.org facilitator or self-hosted')

    console.print()
    console.print(Panel(features_table, border_style="bright_green", box=box.ROUNDED))
    console.print()
    console.print(Panel(setup_table, border_style="bright_green", box=box.ROUNDED))
    console.print()
    console.print(
        "[dim]Stablecoin Payment Gateway — self-hosted x402 merchant stack. Set your payout address in config.json → merchant.pay_to_address.[/]"
    )
    console.print()
    console.print("[dim]Contact:[/] [bright_blue]0x4Bb3c7dB378447F2d9af791D4B7B3E4B3Df53b48[/] (ETH/EVM)")
    console.print()
