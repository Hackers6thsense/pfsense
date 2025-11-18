import time
import threading
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich.text import Text

def get_log_tail(log_file_path, n=10):
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) >= n else lines
    except Exception:
        return []

from rich.spinner import Spinner
from rich.align import Align

def run_dashboard(oblivion, refresh_rate=1.0):
    import threading
    import sys
    import click

    console = Console()
    assets = oblivion.assets
    playbook = oblivion.attack_playbook
    log_path = getattr(oblivion.log_file, "name", None)
    engagement_id = getattr(oblivion.policy.engagement, "engagement_id", "unknown")
    running = True
    spinner_text = "[cyan]Attack(s) running..."
    spinner = Spinner("dots", text=spinner_text)

    # Keyboard thread logic
    def keypress_listener():
        nonlocal running
        while running:
            try:
                key = click.getchar()
                if key == "s":
                    oblivion.stop_all_attacks()
                    console.print("[yellow][i] Stop signal sent to all attacks.[/i][/yellow]")
                elif key == "q":
                    running = False
                    console.print("[cyan][i] Exiting dashboard.[/i][/cyan]")
            except Exception:
                pass

    keyboard_thread = threading.Thread(target=keypress_listener, daemon=True)
    keyboard_thread.start()

    def make_layout():
        # Engagement Info Panel
        info = Table.grid(padding=1)
        info.add_column(justify="left")
        info.add_column(justify="left")
        info.add_row("Engagement ID", str(engagement_id))
        info.add_row("Intelligence", f"{oblivion.intelligence:.2f}")
        info.add_row("Location", str(getattr(oblivion, "current_location", "unknown")))
        active_cnt = sum(1 for t in oblivion.active_threads if t.is_alive())
        info.add_row("Active Threads", str(active_cnt))
        info_panel = Panel(info, title="Engagement", border_style="blue")

        # Asset Stats Panel
        asset_summary = assets.get_summary()
        hosts_cnt = len(asset_summary.get("hosts", []))
        services_cnt = len(asset_summary.get("services", []))
        asset_stats = Table.grid()
        asset_stats.add_column()
        asset_stats.add_column()
        asset_stats.add_row("Hosts", str(hosts_cnt))
        asset_stats.add_row("Services", str(services_cnt))
        asset_panel = Panel(asset_stats, title="Assets", border_style="green")

        # Playbook Panel with color per row
        ptable = Table(title="Attack Playbook", border_style="magenta")
        ptable.add_column("Technique", style="bold cyan")
        ptable.add_column("Success", justify="right")
        ptable.add_column("Failure", justify="right")
        ptable.add_column("Attempts", justify="right")
        for tech, stats in playbook.items():
            succ, fail = stats.get("success", 0), stats.get("failure", 0)
            attempts = stats.get("attempts", 0)
            if succ > 0:
                style = "green"
            elif fail > 0:
                style = "red"
            else:
                style = "yellow"
            ptable.add_row(
                f"[{style}]{tech}[/{style}]",
                f"[{style}]{succ}[/{style}]",
                f"[{style}]{fail}[/{style}]",
                f"[{style}]{attempts}[/{style}]"
            )
        playbook_panel = Panel(ptable, border_style="magenta")

        # Log Tail Panel
        log_lines = get_log_tail(log_path, n=10) if log_path else []
        log_text = Text("".join(log_lines), style="yellow")
        log_panel = Panel(log_text, title="Recent Events (Log Tail)", border_style="yellow")

        # Spinner if any attack threads alive
        spinner_panel = None
        if active_cnt > 0:
            # Center spinner above dashboard
            spinner_panel = Panel(Align.center(spinner.renderable, vertical="middle"), border_style="cyan")
        else:
            spinner_panel = Panel("[green]No attacks running.", border_style="cyan")

        # Compose Layout
        layout = Layout()
        layout.split(
            Layout(name="spinner", size=3),
            Layout(name="upper", size=6),
            Layout(name="middle", size=8),
            Layout(name="lower", ratio=1),
            Layout(name="hint", size=2)
        )
        layout["spinner"].update(spinner_panel)
        layout["upper"].split_row(
            Layout(info_panel, name="info"),
            Layout(asset_panel, name="assets"),
        )
        layout["middle"].update(playbook_panel)
        layout["lower"].update(log_panel)
        layout["hint"].update(Text("Shortcuts: [s]top all, [q]uit", style="dim cyan"))
        return layout

    try:
        with Live(make_layout(), refresh_per_second=int(1/refresh_rate) if refresh_rate < 1 else 1, screen=True, console=console) as live:
            while running:
                live.update(make_layout())
                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        print("\n[+] Dashboard closed")

def run_blueteam_view(oblivion, refresh_rate=2.0):
    console = Console()
    assets = oblivion.assets
    playbook = oblivion.attack_playbook
    engagement_id = getattr(oblivion.policy.engagement, "engagement_id", "unknown")

    def make_layout():
        # Engagement Info Panel
        info = Table.grid(padding=1)
        info.add_column(justify="left")
        info.add_column(justify="left")
        info.add_row("Engagement ID", str(engagement_id))
        info.add_row("Intelligence", f"{oblivion.intelligence:.2f}")
        info.add_row("Location", str(getattr(oblivion, "current_location", "unknown")))
        info.add_row("Active Threads", str(sum(1 for t in oblivion.active_threads if t.is_alive())))
        info_panel = Panel(info, title="Engagement", border_style="blue")

        # Asset Stats Panel
        asset_summary = assets.get_summary()
        hosts_cnt = len(asset_summary.get("hosts", []))
        services_cnt = len(asset_summary.get("services", []))
        asset_stats = Table.grid()
        asset_stats.add_column()
        asset_stats.add_column()
        asset_stats.add_row("Hosts", str(hosts_cnt))
        asset_stats.add_row("Services", str(services_cnt))
        asset_panel = Panel(asset_stats, title="Assets", border_style="green")

        # Playbook Panel (counts only)
        ptable = Table(title="Playbook Summary", border_style="magenta")
        ptable.add_column("Technique", style="bold cyan")
        ptable.add_column("Attempts", justify="right")
        for tech, stats in playbook.items():
            ptable.add_row(
                tech,
                str(stats.get("attempts", 0))
            )
        playbook_panel = Panel(ptable, border_style="magenta")

        layout = Layout()
        layout.split(
            Layout(name="upper", size=6),
            Layout(name="middle", size=8),
            Layout(name="lower", ratio=1)
        )
        layout["upper"].split_row(
            Layout(info_panel, name="info"),
            Layout(asset_panel, name="assets"),
        )
        layout["middle"].update(playbook_panel)
        layout["lower"].update(Panel("[blue]This is a blue-team view. No exploit details shown.", border_style="blue"))
        return layout

    try:
        with Live(make_layout(), refresh_per_second=int(1/refresh_rate) if refresh_rate < 1 else 1, screen=True, console=console) as live:
            while True:
                live.update(make_layout())
                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        print("\n[+] Blue-Team View closed")