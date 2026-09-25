# -*- coding: utf-8 -*-
"""Bot actions for Stablecoin Payment Gateway — invoicing, payment links, webhooks, x402 paywalls, settlement monitoring and key management.

Realistic simulation layer with Rich output.
"""

import random
import time
from datetime import datetime

from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from pipeline.ui import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    separator,
)


_CHAINS = [
    ("Ethereum", "ETH", 12), ("Base", "ETH", 12), ("BNB Chain", "BNB", 15),
    ("Polygon", "POL", 64), ("Arbitrum", "ETH", 12), ("Tron", "TRX", 19),
    ("Solana", "SOL", 32), ("TON", "TON", 12),
]

_TOKENS = [("USDC", 6), ("USDT", 6), ("PYUSD", 6), ("DAI", 18)]

_EVENTS = [
    "invoice.created", "invoice.paid", "invoice.settled",
    "invoice.expired", "invoice.underpaid", "payout.completed",
]

_SCOPES = ["invoices:write", "invoices:read", "links:write", "webhooks:read", "reports:read"]


def _random_address() -> str:
    return f"0x{random.randbytes(20).hex()}"


def _invoice_id() -> str:
    return f"inv_{random.randbytes(8).hex()}"


def _link_slug() -> str:
    return f"pay_{random.randbytes(5).hex()}"


def _amount() -> str:
    return f"{random.uniform(5, 2500):,.2f}"


def _state_badge(state: str) -> str:
    colors = {
        "pending": "yellow", "confirming": "bright_blue",
        "settled": "bright_green", "expired": "dim",
    }
    return f"[{colors.get(state, 'white')}]{state}[/{colors.get(state, 'white')}]"


def _invoice_card(cfg):
    chain = random.choice(_CHAINS)
    token = random.choice(_TOKENS)
    inv = _invoice_id()
    amt = _amount()
    addr = _random_address()
    ttl = cfg.get("invoice", {}).get("ttl_minutes", 30)
    return [
        ("Invoice ID", inv),
        ("Amount", f"{amt} {token[0]}"),
        ("Chain", chain[0]),
        ("Deposit Address", addr),
        ("Confirmations", f"0/{chain[2]}"),
        ("Expires In", f"{ttl} min"),
        ("Checkout URL", f"https://pay.example.com/i/{inv}"),
    ]


def _invoice_row():
    chain = random.choice(_CHAINS)
    token = random.choice(_TOKENS)
    state = random.choice(["pending", "confirming", "settled", "settled", "expired"])
    confs = chain[2] if state == "settled" else (0 if state in ("pending", "expired") else random.randint(1, chain[2] - 1))
    return (_invoice_id(), chain[0], token[0], _amount(),
            f"{confs}/{chain[2]}", _state_badge(state))


def _link_row():
    clicks = random.randint(5, 400)
    conv = random.randint(0, clicks)
    state = random.choice(["active", "active", "active", "disabled"])
    badge = "[bright_green]active[/]" if state == "active" else "[dim]disabled[/]"
    return (f"https://pay.example.com/l/{_link_slug()}",
            f"{_amount()} USDC", str(clicks), str(conv), badge)


def _webhook_rows(cfg):
    out = []
    for event in _EVENTS:
        attempts = random.randint(1, 3)
        status = "[bright_green]200 OK[/]" if random.random() > 0.12 else "[red]Timeout[/]"
        latency = f"{random.randint(60, 480)} ms"
        out.append((event, f"https://merchant.example.com/hooks/{event.split('.')[0]}",
                    str(attempts), status, latency))
    return out


def _key_rows():
    out = []
    for i in range(random.randint(3, 5)):
        kid = f"mk_live_{random.randbytes(6).hex()}"
        created = "2026-0%d-%02d" % (random.randint(1, 9), random.randint(1, 28))
        scopes = ", ".join(random.sample(_SCOPES, random.randint(2, 4)))
        status = "[bright_green]Active[/]" if i else "[dim]Rotated[/]"
        out.append((kid, created, scopes, status))
    return out


def _x402_rows(cfg):
    x = cfg.get("x402", {})
    routes = x.get("paywall_routes", ["/api/premium"])
    return [
        ("Facilitator", x.get("facilitator_url", "https://x402.org/facilitator"), "Verification & settlement"),
        ("Scheme", x.get("scheme", "exact"), "exact / upto / batch-settlement"),
        ("Paywall Routes", ", ".join(routes), "402-gated endpoints"),
        ("Payment Header", "X-PAYMENT", "Client → server payload"),
        ("Response Header", "PAYMENT-RESPONSE", "Settlement receipt"),
        ("Networks", "base, ethereum, polygon, arbitrum", "Server-controlled allowlist"),
    ]


def _chain_rows(cfg):
    out = []
    chains = cfg.get("chains", {})
    for name, native, confs in _CHAINS:
        key = name.lower().replace(" ", "_").replace("bnb_chain", "bsc")
        ccfg = chains.get(key, {})
        enabled = ccfg.get("enabled", True)
        rpc = ccfg.get("rpc", "public RPC")
        rpc = rpc[:28] + "..." if len(rpc) > 31 else rpc
        status = "[bright_green]Enabled[/]" if enabled else "[dim]Disabled[/]"
        tokens = ", ".join(t for t, _ in _TOKENS[:2]) if enabled else "—"
        out.append((name, tokens, str(confs), rpc, status))
    return out


def _export_rows(cfg):
    exp = cfg.get("export", {})
    fmt = exp.get("default_format", "csv")
    out_dir = exp.get("output_directory", "./exports")
    fname = "settlements_%s.%s" % (datetime.now().strftime("%Y%m%d_%H%M%S"), fmt)
    return [
        ("Filename", fname),
        ("Format", fmt.upper()),
        ("Invoices", str(random.randint(40, 900))),
        ("Size", f"{random.randint(12, 480)} KB"),
        ("Path", f"{out_dir}/{fname}"),
    ]


def action_create_invoice(cfg: dict):
    """Create a fixed-amount invoice with a unique deposit address (simulation)."""
    console.print()
    print_info('Merchant: demo store · Mode: live')
    print_info('Non-custodial: funds settle directly to your wallet')
    separator()
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Creating invoice...', total=4)
        for step_label in ['Deriving unique deposit address (xpub)...',
         'Registering invoice on the gateway...',
         'Starting confirmation watcher...',
         'Building checkout page & QR payload...']:
            progress.update(task, description=step_label)
            time.sleep(0.35)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.ROUNDED,
        title="[bold bright_green]  INVOICE  [/]",
    )
    table.add_column('Property', style='bright_blue')
    table.add_column('Value', justify='right', style='bright_white')

    for row in _invoice_card(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Invoice created. Watcher is live.')
    print_info('Customer pays to the deposit address — webhook fires on confirmation.')


def action_payment_links(cfg: dict):
    """List shareable payment links with conversion stats (simulation)."""
    console.print()
    count = random.randint(4, 7)
    print_info('Payment links are reusable checkout URLs for products or donations')
    separator()
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Loading links...', total=2)
        for step_label in ['Loading payment links...', 'Aggregating click & conversion stats...']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.ROUNDED,
        title="[bold bright_green]  PAYMENT LINKS  [/]",
    )
    table.add_column('URL', style='bright_cyan')
    table.add_column('Amount', justify='right', style='bright_white')
    table.add_column('Clicks', justify='right', style='dim')
    table.add_column('Paid', justify='right', style='bright_green')
    table.add_column('Status', justify='center')

    for row in [_link_row() for _ in range(count)]:
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Links loaded.')
    print_info('Create links programmatically via POST /v1/links.')


def action_webhooks(cfg: dict):
    """Show webhook delivery status for recent events (simulation)."""
    console.print()
    print_info('All webhook payloads are HMAC-SHA256 signed (X-Signature-256 header)')
    separator()
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Checking deliveries...', total=3)
        for step_label in ['Querying delivery log...', 'Verifying signatures...', 'Computing latencies...']:
            progress.update(task, description=step_label)
            time.sleep(0.35)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.ROUNDED,
        title="[bold bright_green]  WEBHOOK DELIVERIES  [/]",
    )
    table.add_column('Event', style='bright_cyan')
    table.add_column('Endpoint', style='dim')
    table.add_column('Attempts', justify='center', style='yellow')
    table.add_column('Status', justify='center')
    table.add_column('Latency', justify='right', style='yellow')

    for row in _webhook_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Failed deliveries retry with backoff: 5s → 30s → 120s.')
    print_info('Configure the endpoint in config.json → merchant.callback_url.')


def action_x402_paywall(cfg: dict):
    """Show x402 paywall configuration (HTTP 402 pay-per-request)."""
    console.print()
    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.ROUNDED,
        title="[bold bright_green]  X402 PAYWALL  [/]",
    )
    table.add_column('Parameter', style='bright_cyan')
    table.add_column('Value', justify='right', style='bright_white')
    table.add_column('Notes', style='dim')

    for row in _x402_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Unpaid requests get HTTP 402 with accepted networks & assets.')
    print_info('Paid requests carry X-PAYMENT and are verified via the facilitator.')


def action_settlement_monitor(cfg: dict):
    """Monitor invoice confirmations and settlement status (simulation)."""
    console.print()
    count = random.randint(6, 10)
    print_info('Watching mempool and confirmed blocks across enabled chains')
    separator()
    with Progress(
        SpinnerColumn(style="bright_blue"),
        TextColumn("[bright_blue]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Polling watchers...', total=3)
        for step_label in ['Polling chain watchers...',
         'Reconciling confirmations...',
         'Updating settlement states...']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
        box=box.ROUNDED,
        title="[bold bright_blue]  SETTLEMENTS  [/]",
    )
    table.add_column('Invoice', style='bright_cyan')
    table.add_column('Chain', style='bright_blue')
    table.add_column('Token', style='yellow')
    table.add_column('Amount', justify='right', style='bright_white')
    table.add_column('Confs', justify='center', style='dim')
    table.add_column('State', justify='center')

    for row in [_invoice_row() for _ in range(count)]:
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Settlement states reconciled.')
    print_info('Settled invoices trigger invoice.settled webhooks automatically.')


def action_api_keys(cfg: dict):
    """Issue and rotate merchant REST API credentials (simulation)."""
    console.print()
    print_info('Merchant API keys authenticate REST calls (Authorization: Bearer)')
    separator()
    with Progress(
        SpinnerColumn(style="bright_yellow"),
        TextColumn("[bright_yellow]{task.description}"),
        BarColumn(bar_width=40, style="yellow", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Rotating keys...', total=3)
        for step_label in ['Loading key registry...', 'Checking rotation policy...', 'Auditing scopes...']:
            progress.update(task, description=step_label)
            time.sleep(0.35)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_yellow",
        border_style="yellow",
        box=box.ROUNDED,
        title="[bold bright_yellow]  MERCHANT API KEYS  [/]",
    )
    table.add_column('Key ID', style='bright_cyan')
    table.add_column('Created', style='dim')
    table.add_column('Scopes', style='bright_white')
    table.add_column('Status', justify='center')

    for row in _key_rows():
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_warning('Store secrets in a password manager — keys are shown once at creation.')
    print_info('Rotate keys every 90 days; old keys enter a 24h grace period.')


def action_chains_tokens(cfg: dict):
    """Show enabled networks, tokens and confirmation policy."""
    console.print()
    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.ROUNDED,
        title="[bold bright_green]  CHAINS & TOKENS  [/]",
    )
    table.add_column('Chain', style='bright_cyan')
    table.add_column('Tokens', style='yellow')
    table.add_column('Confs', justify='center', style='dim')
    table.add_column('RPC', style='dim')
    table.add_column('Status', justify='center')

    for row in _chain_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Edit chain endpoints and tokens in config.json → chains / tokens.')


__all__ = ['action_create_invoice',
 'action_payment_links',
 'action_webhooks',
 'action_x402_paywall',
 'action_settlement_monitor',
 'action_api_keys',
 'action_chains_tokens']
