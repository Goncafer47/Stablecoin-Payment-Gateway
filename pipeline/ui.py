# -*- coding: utf-8 -*-
"""
Rich console UI components for Stablecoin Payment Gateway.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

console = Console()

VERSION = "2.6.0"
TITLE = "Stablecoin Payment Gateway"


def print_banner():
    console.print()
    console.print(
        Panel(
            f"[bold white]{TITLE}[/bold white] [dim]v{VERSION}[/dim]\n"
            "[dim]Self-Hosted x402 Stablecoin Payment Gateway[/dim]",
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print()


def show_menu_table(menu_items):
    """Display menu table and return user choice."""
    table = Table(
        title=f"[bold bright_green]{TITLE}[/bold bright_green]",
        box=box.DOUBLE_EDGE,
        border_style="bright_green",
        title_style="bold white",
        show_header=True,
        header_style="bold bright_white",
        padding=(0, 2),
    )
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Icon", style="white", justify="center", width=4)
    table.add_column("Action", style="white", min_width=30)
    table.add_column("Description", style="dim", min_width=30)

    for idx, icon, action, desc in menu_items:
        style = "bold red" if action.lower() == "exit" else "white"
        table.add_row(idx, icon, f"[{style}]{action}[/{style}]", desc)

    console.print()
    console.print(table)
    console.print()

    choice = console.input("[bold bright_green]  Select option >[/] ").strip()
    return choice


def print_success(message):
    console.print(f"  [bold green]✓[/bold green] {message}")


def print_error(message):
    console.print(f"  [bold red]✗[/bold red] {message}")


def print_info(message):
    console.print(f"  [bold blue]ℹ[/bold blue] {message}")


def print_warning(message):
    console.print(f"  [bold yellow]⚠[/bold yellow] {message}")


def separator():
    console.print("[dim]─" * 60 + "[/dim]")


def progress_bar(description, total=100, transient=False):
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold bright_green]{task.description}"),
        BarColumn(bar_width=40, complete_style="bright_green", finished_style="bright_green"),
        TextColumn("[bold]{task.percentage:>3.0f}%"),
        console=console,
        transient=transient,
    )


def show_simple_list(title, items):
    """Display a simple list of items with a title."""
    if title:
        console.print(f"\n[bold bright_green]{title}[/bold bright_green]")
    for item in items:
        console.print(f"  [bright_white]•[/] {item}")
    console.print()
