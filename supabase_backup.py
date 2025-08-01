#!/usr/bin/env python3
# supabase_backup.py

import os
import subprocess
from datetime import datetime
from getpass import getpass

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()

def gather_connection_info():
    console.rule("[bold blue]Supabase Backup Configuration[/]")
    if Confirm.ask("Do you have a full Supabase DATABASE_URL?"):
        return Prompt.ask("Paste your DATABASE_URL (postgres://…)", password=False)

    host = Prompt.ask("Host", default="db.YOUR-PROJECT.supabase.co")
    port = Prompt.ask("Port", default="5432")
    db   = Prompt.ask("Database name", default="postgres")
    user = Prompt.ask("Username", default="postgres")
    pwd  = getpass("Password: ")
    return f"postgres://{user}:{pwd}@{host}:{port}/{db}"

def choose_output_dir():
    default = os.getcwd()
    out = Prompt.ask("Output directory", default=default)
    if not os.path.isdir(out):
        console.print(f"[red]Error:[/] '{out}' is not a directory.")
        raise SystemExit(1)
    return out

def run_backup(db_url: str, out_dir: str):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(out_dir, f"supabase_backup_{now}.dump")
    cmd = [
        "pg_dump",
        db_url,
        "--format", "custom",
        "--file", filename,
    ]

    console.print(Panel(f"[green]Backing up to[/] [bold]{filename}[/]\n", title="Starting Backup"))

    with console.status("Running pg_dump…", spinner="dots"):
        subprocess.run(cmd, check=True)

    console.print(Panel(f"[bold green]Success![/] Backup saved to:\n{filename}", title="Done"))

def main():
    console.clear()
    db_url = gather_connection_info()
    out_dir = choose_output_dir()
    run_backup(db_url, out_dir)
    if Confirm.ask("Generate a cron entry for nightly 03:30 backup?"):
        script = os.path.abspath(__file__)
        cron  = f"30 3 * * * /usr/bin/env python3 {script} >> {os.path.join(out_dir,'backup.log')} 2>&1"
        console.print(Panel(cron, title="Add this line to your crontab (`crontab -e`)"))

if __name__ == "__main__":
    main()
