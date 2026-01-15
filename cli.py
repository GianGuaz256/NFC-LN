#!/usr/bin/env python3
"""Command-line interface for LN-NFC application."""

import sys
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from src.config import load_config
from src.main import Application

# Initialize CLI app
app = typer.Typer(
    name="ln-nfc",
    help="Lightning Network NFC Payment System",
    add_completion=False,
)

console = Console()


def get_app() -> Application:
    """Get initialized application instance."""
    try:
        config = load_config()
        application = Application(config)
        application.initialize()
        return application
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to initialize application: {e}")
        raise typer.Exit(1)


@app.command()
def load_tag(
    amount: int = typer.Option(..., "--amount", "-a", help="Amount in satoshis"),
    uses: int = typer.Option(1, "--uses", "-u", help="Number of times link can be used"),
    title: str = typer.Option("Lightning Gift Card", "--title", "-t", help="Title for the withdraw link"),
    timeout: float = typer.Option(10.0, "--timeout", help="Timeout for waiting for tag (seconds)"),
):
    """
    Load an NFC tag with a new LNURL-withdraw link.
    
    Creates a withdraw link in LNbits and writes it to an NFC tag.
    """
    console.print(f"\n[bold cyan]Loading NFC Tag[/bold cyan]")
    console.print(f"Amount: [green]{amount}[/green] sats")
    console.print(f"Uses: [green]{uses}[/green]")
    console.print(f"Title: [green]{title}[/green]\n")
    
    application = get_app()
    
    try:
        with console.status("[bold yellow]Creating withdraw link..."):
            result = application.tag_loader.load_tag(
                amount=amount,
                title=title,
                uses=uses,
                timeout=timeout,
            )
        
        if result.get("success"):
            console.print("\n[bold green]✓ Tag loaded successfully![/bold green]\n")
            
            # Display result in a table
            table = Table(show_header=False, box=None)
            table.add_row("Tag UID:", f"[cyan]{result['tag_uid']}[/cyan]")
            table.add_row("Link ID:", f"[cyan]{result['link_id']}[/cyan]")
            table.add_row("Amount:", f"[green]{result['amount']} sats[/green]")
            table.add_row("Uses:", f"[green]{result['uses']}[/green]")
            table.add_row("LNURL:", f"[yellow]{result['lnurl'][:50]}...[/yellow]")
            
            console.print(table)
            console.print()
        else:
            console.print(f"[red]✗ Failed to load tag:[/red] {result.get('error')}")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def read_tag(
    timeout: float = typer.Option(10.0, "--timeout", help="Timeout for waiting for tag (seconds)"),
):
    """
    Read LNURL from an NFC tag.
    
    Displays the LNURL and validates it.
    """
    console.print("\n[bold cyan]Reading NFC Tag[/bold cyan]")
    console.print(f"Place tag near reader (timeout: {timeout}s)...\n")
    
    application = get_app()
    
    try:
        with console.status("[bold yellow]Waiting for tag..."):
            result = application.tag_loader.read_tag(timeout=timeout)
        
        if result.get("success"):
            console.print("\n[bold green]✓ Tag read successfully![/bold green]\n")
            
            # Display result
            table = Table(show_header=False, box=None)
            table.add_row("Tag UID:", f"[cyan]{result['tag_uid']}[/cyan]")
            table.add_row("LNURL:", f"[yellow]{result['lnurl']}[/yellow]")
            table.add_row("Valid:", f"[{'green' if result['valid'] else 'red'}]{result['valid']}[/{'green' if result['valid'] else 'red'}]")
            
            if result.get("params"):
                params = result["params"]
                if params.get("url"):
                    table.add_row("URL:", f"[blue]{params['url']}[/blue]")
                if params.get("type"):
                    table.add_row("Type:", f"[magenta]{params['type']}[/magenta]")
            
            console.print(table)
            console.print()
        else:
            console.print(f"[red]✗ Failed to read tag:[/red] {result.get('error')}")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def clear_tag(
    timeout: float = typer.Option(10.0, "--timeout", help="Timeout for waiting for tag (seconds)"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Clear/format an NFC tag.
    
    Removes all data from the tag.
    """
    if not confirm:
        confirm = typer.confirm("Are you sure you want to clear the tag?")
        if not confirm:
            console.print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0)
    
    console.print("\n[bold cyan]Clearing NFC Tag[/bold cyan]")
    console.print(f"Place tag near reader (timeout: {timeout}s)...\n")
    
    application = get_app()
    
    try:
        with console.status("[bold yellow]Waiting for tag..."):
            result = application.tag_loader.clear_tag(timeout=timeout)
        
        if result.get("success"):
            console.print(f"\n[bold green]✓ Tag cleared successfully![/bold green]")
            console.print(f"Tag UID: [cyan]{result['tag_uid']}[/cyan]\n")
        else:
            console.print(f"[red]✗ Failed to clear tag:[/red] {result.get('error')}")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def status():
    """
    Check system status and LNbits connection.
    
    Displays wallet balance and connection information.
    """
    console.print("\n[bold cyan]System Status[/bold cyan]\n")
    
    application = get_app()
    
    try:
        # Check LNbits connection
        with console.status("[bold yellow]Checking LNbits connection..."):
            wallet_info = application.lnbits_client.get_wallet_info()
            balance = wallet_info.get("balance", 0)
        
        # Display status
        table = Table(show_header=False, box=None)
        table.add_row("LNbits URL:", f"[blue]{application.config.lnbits_url}[/blue]")
        table.add_row("Connection:", "[green]✓ Connected[/green]")
        table.add_row("Wallet:", f"[cyan]{wallet_info.get('name', 'Unknown')}[/cyan]")
        table.add_row("Balance:", f"[green]{balance // 1000} sats[/green] ({balance} msat)")
        table.add_row("NFC Interface:", f"[magenta]{application.config.nfc_interface.upper()}[/magenta]")
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def daemon(
    poll_interval: Optional[float] = typer.Option(None, "--poll-interval", help="Polling interval in seconds"),
):
    """
    Run in daemon mode (continuous payment processing).
    
    Continuously listens for NFC tags and processes payments.
    Press Ctrl+C to stop.
    """
    console.print("\n[bold cyan]Starting Daemon Mode[/bold cyan]\n")
    
    try:
        config = load_config()
        
        if poll_interval is not None:
            config.poll_interval = poll_interval
        
        console.print(f"Poll interval: [green]{config.poll_interval}s[/green]")
        console.print(f"Rate limit: [green]{config.rate_limit_seconds}s[/green]")
        console.print("\n[yellow]Listening for NFC tags... (Press Ctrl+C to stop)[/yellow]\n")
        
        application = Application(config)
        application.run_daemon()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    timeout: float = typer.Option(10.0, "--timeout", help="Timeout for waiting for tag (seconds)"),
):
    """
    Get detailed information about an NFC tag.
    
    Displays tag type, UID, NDEF data, and LNURL if present.
    """
    console.print("\n[bold cyan]NFC Tag Information[/bold cyan]")
    console.print(f"Place tag near reader (timeout: {timeout}s)...\n")
    
    application = get_app()
    
    try:
        with console.status("[bold yellow]Waiting for tag..."):
            info = application.tag_loader.get_tag_info(timeout=timeout)
        
        console.print("\n[bold green]✓ Tag detected![/bold green]\n")
        
        # Display tag info
        table = Table(show_header=False, box=None)
        table.add_row("Present:", f"[green]{info.get('present')}[/green]")
        table.add_row("UID:", f"[cyan]{info.get('uid')}[/cyan]")
        table.add_row("UID Length:", f"{info.get('uid_length')} bytes")
        
        if info.get("type"):
            table.add_row("Type:", f"[magenta]{info['type']}[/magenta]")
        
        if info.get("ndef"):
            ndef = info["ndef"]
            table.add_row("NDEF Valid:", f"[{'green' if ndef.get('valid') else 'red'}]{ndef.get('valid')}[/{'green' if ndef.get('valid') else 'red'}]")
            table.add_row("NDEF Size:", f"{ndef.get('size')} bytes")
            table.add_row("NDEF Records:", f"{ndef.get('records')}")
        
        if info.get("lnurl"):
            table.add_row("LNURL:", f"[yellow]{info['lnurl'][:50]}...[/yellow]")
            table.add_row("LNURL Valid:", f"[{'green' if info.get('lnurl_valid') else 'red'}]{info.get('lnurl_valid')}[/{'green' if info.get('lnurl_valid') else 'red'}]")
        
        console.print(table)
        console.print()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def list_links(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of links to display"),
):
    """
    List all LNURL-withdraw links in LNbits.
    
    Shows active withdraw links with their details.
    """
    console.print("\n[bold cyan]LNURL-Withdraw Links[/bold cyan]\n")
    
    application = get_app()
    
    try:
        with console.status("[bold yellow]Fetching links from LNbits..."):
            links = application.lnbits_client.list_withdraw_links()
        
        if not links:
            console.print("[yellow]No withdraw links found[/yellow]\n")
            return
        
        # Display links in a table
        table = Table(show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Amount", style="green")
        table.add_column("Uses", style="yellow")
        table.add_column("Used", style="magenta")
        
        for link in links[:limit]:
            link_id = link.get("id", "")[:8]
            title = link.get("title", "")[:30]
            amount = link.get("max_withdrawable", 0) // 1000
            uses = link.get("uses", 0)
            used = link.get("used", 0)
            
            table.add_row(
                link_id,
                title,
                f"{amount} sats",
                str(uses),
                str(used),
            )
        
        console.print(table)
        console.print(f"\nShowing {min(len(links), limit)} of {len(links)} link(s)\n")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        application.cleanup()


@app.command()
def version():
    """Display version information."""
    from src import __version__
    
    console.print(Panel(
        f"[bold cyan]LN-NFC[/bold cyan]\n"
        f"Version: [green]{__version__}[/green]\n"
        f"Lightning Network NFC Payment System",
        title="Version Info",
        border_style="cyan",
    ))


def main():
    """Main CLI entry point."""
    try:
        app()
    except Exception as e:
        console.print(f"\n[red]Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
