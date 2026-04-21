"""
CLI entry point for the trading bot.
Enhanced UX with Typer, Rich tables, interactive prompts, and color-coded output.
"""

import os
import sys
from typing import Optional

# Fix Windows console encoding for Unicode/Rich output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.orders import OrderManager, OrderResult

# ── App Setup ────────────────────────────────────────────────────────────────

load_dotenv()
logger = setup_logging(level="DEBUG")
console = Console(force_terminal=True)

app = typer.Typer(
    name="trading-bot",
    help="[bold]Binance Futures Testnet Trading Bot[/bold] -- Place MARKET, LIMIT, and STOP-LIMIT orders.",
    add_completion=False,
    rich_markup_mode="rich",
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_client() -> BinanceClient:
    """Create and return a BinanceClient from environment variables."""
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret or api_key == "your_api_key_here":
        console.print(
            Panel(
                "[bold red]API credentials not configured![/bold red]\n\n"
                "1. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan]\n"
                "2. Add your Binance Futures Testnet API key and secret\n"
                "3. Get credentials at: [link=https://testnet.binancefuture.com]testnet.binancefuture.com[/link]",
                title="⚠️  Setup Required",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


def _get_order_manager() -> OrderManager:
    """Create and return an OrderManager."""
    client = _get_client()
    return OrderManager(client)


def _display_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
    stop_price: Optional[str],
) -> None:
    """Display a formatted order request summary table."""
    table = Table(
        title="📋 Order Request Summary",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold white",
    )
    table.add_column("Parameter", style="dim white", width=15)
    table.add_column("Value", style="bold green")

    table.add_row("Symbol", symbol)
    table.add_row("Side", f"[bold {'green' if side == 'BUY' else 'red'}]{side}[/]")
    table.add_row("Type", order_type)
    table.add_row("Quantity", quantity)

    if price:
        table.add_row("Price", price)
    if stop_price:
        table.add_row("Stop Price", stop_price)

    console.print()
    console.print(table)


def _display_order_result(result: OrderResult) -> None:
    """Display a formatted order result."""
    if result.success:
        table = Table(
            title="✅ Order Placed Successfully",
            show_header=True,
            header_style="bold green",
            border_style="green",
            title_style="bold green",
        )
        table.add_column("Field", style="dim white", width=18)
        table.add_column("Value", style="bold white")

        summary = result.to_summary_dict()
        field_labels = {
            "orderId": "Order ID",
            "clientOrderId": "Client Order ID",
            "symbol": "Symbol",
            "side": "Side",
            "type": "Type",
            "status": "Status",
            "origQty": "Original Qty",
            "executedQty": "Executed Qty",
            "price": "Price",
            "avgPrice": "Avg Price",
        }

        for key, label in field_labels.items():
            value = str(summary.get(key, "N/A"))
            if key == "side":
                value = f"[bold {'green' if value == 'BUY' else 'red'}]{value}[/]"
            elif key == "status":
                color = "green" if value in ("FILLED", "NEW") else "yellow"
                value = f"[bold {color}]{value}[/]"
            table.add_row(label, value)

        console.print()
        console.print(table)
        console.print()
        console.print("[bold green]🎉 Order executed successfully![/bold green]")

    else:
        console.print()
        console.print(
            Panel(
                f"[bold red]{result.error_message}[/bold red]",
                title="❌ Order Failed",
                border_style="red",
            )
        )


def _display_banner() -> None:
    """Display the application banner."""
    banner = Text()
    banner.append("╔══════════════════════════════════════════════╗\n", style="cyan")
    banner.append("║    ", style="cyan")
    banner.append("🤖 Binance Futures Trading Bot", style="bold white")
    banner.append("         ║\n", style="cyan")
    banner.append("║    ", style="cyan")
    banner.append("   Testnet (USDT-M) Edition", style="dim white")
    banner.append("           ║\n", style="cyan")
    banner.append("╚══════════════════════════════════════════════╝", style="cyan")
    console.print(banner)


# ── CLI Commands ─────────────────────────────────────────────────────────────


@app.command("order")
def place_order_cmd(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair (e.g., BTCUSDT)"),
    side: str = typer.Option(..., "--side", "-S", help="Order side: BUY or SELL"),
    order_type: str = typer.Option(
        ..., "--type", "-t", help="Order type: MARKET, LIMIT, or STOP_LIMIT"
    ),
    quantity: str = typer.Option(..., "--quantity", "-q", help="Order quantity (e.g., 0.001)"),
    price: Optional[str] = typer.Option(
        None, "--price", "-p", help="Limit price (required for LIMIT & STOP_LIMIT)"
    ),
    stop_price: Optional[str] = typer.Option(
        None, "--stop-price", "-sp", help="Stop trigger price (required for STOP_LIMIT)"
    ),
    time_in_force: Optional[str] = typer.Option(
        None, "--tif", help="Time in force: GTC, IOC, FOK (default: GTC)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """
    Place a new order on Binance Futures Testnet.

    Examples:

        # Market buy 0.01 BTC
        python cli.py order -s BTCUSDT -S BUY -t MARKET -q 0.01

        # Limit sell 0.5 ETH at $2000
        python cli.py order -s ETHUSDT -S SELL -t LIMIT -q 0.5 -p 2000

        # Stop-Limit buy 0.01 BTC, stop at $65000, limit at $65500
        python cli.py order -s BTCUSDT -S BUY -t STOP_LIMIT -q 0.01 -p 65500 -sp 65000
    """
    _display_banner()

    # Display request summary
    _display_request_summary(symbol, side, order_type, quantity, price, stop_price)

    # Confirm before placing
    if not yes:
        console.print()
        if not Confirm.ask("[bold yellow]Proceed with this order?[/bold yellow]"):
            console.print("[dim]Order cancelled by user.[/dim]")
            raise typer.Exit()

    console.print()
    console.print("[dim]Connecting to Binance Futures Testnet...[/dim]")

    # Place the order
    manager = _get_order_manager()
    result = manager.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
    )

    _display_order_result(result)

    logger.info(
        "CLI order command completed — success=%s orderId=%s",
        result.success,
        result.order_id,
    )


@app.command("interactive")
def interactive_mode() -> None:
    """
    Launch interactive order placement mode with guided prompts.

    Walk through each parameter step-by-step with validation feedback.
    """
    _display_banner()
    console.print()
    console.print(
        Panel(
            "[bold]Interactive Order Mode[/bold]\n"
            "[dim]Follow the prompts to place an order step by step.[/dim]",
            border_style="cyan",
        )
    )

    # Symbol
    symbol = Prompt.ask(
        "\n[bold cyan]Symbol[/bold cyan] [dim](e.g., BTCUSDT)[/dim]"
    ).strip().upper()

    # Side
    side = Prompt.ask(
        "[bold cyan]Side[/bold cyan]",
        choices=["BUY", "SELL"],
    )

    # Order type
    order_type = Prompt.ask(
        "[bold cyan]Order Type[/bold cyan]",
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
    )

    # Quantity
    quantity = Prompt.ask("[bold cyan]Quantity[/bold cyan]")

    # Price (conditional)
    price = None
    if order_type in ("LIMIT", "STOP_LIMIT"):
        price = Prompt.ask("[bold cyan]Limit Price[/bold cyan]")

    # Stop price (conditional)
    stop_price = None
    if order_type == "STOP_LIMIT":
        stop_price = Prompt.ask("[bold cyan]Stop Trigger Price[/bold cyan]")

    # Time in force (conditional)
    time_in_force = None
    if order_type in ("LIMIT", "STOP_LIMIT"):
        time_in_force = Prompt.ask(
            "[bold cyan]Time in Force[/bold cyan]",
            choices=["GTC", "IOC", "FOK"],
            default="GTC",
        )

    # Show summary and confirm
    _display_request_summary(symbol, side, order_type, quantity, price, stop_price)

    console.print()
    if not Confirm.ask("[bold yellow]Place this order?[/bold yellow]"):
        console.print("[dim]Order cancelled.[/dim]")
        raise typer.Exit()

    # Fetch current price for context
    console.print()
    console.print("[dim]Connecting to Binance Futures Testnet...[/dim]")

    manager = _get_order_manager()

    # Show current market price
    current_price = manager.get_current_price(symbol)
    if current_price:
        console.print(f"[dim]Current {symbol} price: [bold cyan]${current_price:,.2f}[/bold cyan][/dim]")

    # Place order
    result = manager.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
    )

    _display_order_result(result)


@app.command("price")
def get_price_cmd(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair (e.g., BTCUSDT)"),
) -> None:
    """Fetch and display the current price for a symbol."""
    _display_banner()

    manager = _get_order_manager()
    current_price = manager.get_current_price(symbol.upper())

    if current_price:
        console.print()
        console.print(
            Panel(
                f"[bold cyan]{symbol.upper()}[/bold cyan]  →  [bold green]${current_price:,.2f}[/bold green]",
                title="💰 Current Price",
                border_style="cyan",
            )
        )
    else:
        console.print("[bold red]Failed to fetch price.[/bold red]")


@app.command("open-orders")
def open_orders_cmd(
    symbol: Optional[str] = typer.Option(
        None, "--symbol", "-s", help="Filter by trading pair"
    ),
) -> None:
    """List all open orders on the testnet account."""
    _display_banner()

    manager = _get_order_manager()
    orders = manager.get_open_orders(symbol.upper() if symbol else None)

    if not orders:
        console.print()
        console.print("[dim]No open orders found.[/dim]")
        return

    table = Table(
        title="📂 Open Orders",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("Order ID", style="bold white")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Type")
    table.add_column("Qty")
    table.add_column("Price")
    table.add_column("Status")

    for order in orders:
        side_color = "green" if order.get("side") == "BUY" else "red"
        table.add_row(
            str(order.get("orderId", "")),
            order.get("symbol", ""),
            f"[{side_color}]{order.get('side', '')}[/{side_color}]",
            order.get("type", ""),
            order.get("origQty", ""),
            order.get("price", ""),
            order.get("status", ""),
        )

    console.print()
    console.print(table)


@app.command("cancel")
def cancel_order_cmd(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair"),
    order_id: int = typer.Option(..., "--order-id", "-o", help="Order ID to cancel"),
) -> None:
    """Cancel an existing open order."""
    _display_banner()

    manager = _get_order_manager()

    console.print()
    if not Confirm.ask(
        f"[bold yellow]Cancel order {order_id} for {symbol.upper()}?[/bold yellow]"
    ):
        console.print("[dim]Cancellation aborted.[/dim]")
        raise typer.Exit()

    result = manager.cancel_order(symbol.upper(), order_id)

    if result:
        console.print(
            Panel(
                f"[bold green]Order {order_id} cancelled successfully![/bold green]",
                border_style="green",
            )
        )
    else:
        console.print("[bold red]Failed to cancel order.[/bold red]")


@app.command("account")
def account_info_cmd() -> None:
    """Display testnet account information."""
    _display_banner()

    client = _get_client()

    try:
        info = client.get_account_info()

        table = Table(
            title="👤 Account Information",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )
        table.add_column("Field", style="dim white", width=22)
        table.add_column("Value", style="bold white")

        table.add_row("Total Wallet Balance", f"${float(info.get('totalWalletBalance', 0)):,.2f}")
        table.add_row("Available Balance", f"${float(info.get('availableBalance', 0)):,.2f}")
        table.add_row("Total Unrealized PnL", f"${float(info.get('totalUnrealizedProfit', 0)):,.2f}")
        table.add_row("Total Margin Balance", f"${float(info.get('totalMarginBalance', 0)):,.2f}")

        # Show non-zero asset balances
        assets = info.get("assets", [])
        non_zero_assets = [a for a in assets if float(a.get("walletBalance", 0)) > 0]

        if non_zero_assets:
            table.add_row("", "")
            table.add_row("[bold]Assets[/bold]", "")
            for asset in non_zero_assets:
                table.add_row(
                    f"  {asset.get('asset', '')}",
                    f"${float(asset.get('walletBalance', 0)):,.2f}",
                )

        console.print()
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Failed to fetch account info: {e}[/bold red]")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
