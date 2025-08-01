#!/usr/bin/env python3
# supabase_backup.py

import os
import shutil
import subprocess
import sys
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()
# Determine this script's path robustly
try:
    SCRIPT_PATH = os.path.abspath(__file__)
except NameError:
    SCRIPT_PATH = os.path.abspath(sys.argv[0])

def remove_cron_job():
    console.rule("[bold blue]Removing Cron Job[/]")
    try:
        existing = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode().splitlines()
    except subprocess.CalledProcessError:
        existing = []
    kept = [line for line in existing if SCRIPT_PATH not in line]
    new_cron = "\n".join(kept) + "\n"
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    proc.communicate(new_cron.encode())
    console.print(f"[green]Cron job removed successfully.[/]")
    sys.exit(0)

def print_intro():
    console.clear()
    console.rule("[bold blue]🔒 Supabase Backup Utility 🔒[/]")
    console.print(
        "This tool creates a custom-format dump of your Supabase Postgres DB\n"
        "via the Transaction Pooler, and can auto-schedule recurring backups.\n\n"
        "What we will do:\n"
        "1. Ask if you want to overwrite the same backup file or timestamp each run\n"
        "2. Collect your Pooler URI \n"
        "3. Choose an output directory (or set BACKUP_DIR env var)\n"
        "4. Perform one backup now\n"
        "5. (OPTIONAL) Install a cron job for automatic recurring backups\n\n"
        "(OPTIONAL) To cancel the cron job, run: [bold]python3 supabase_backup.py --remove-cron[/bold]\n",
        style="bold"
    )

def check_pg_dump():
    if not shutil.which("pg_dump"):
        console.print(Panel.fit(
            "[red]Error:[/] pg_dump not found.\n"
            "• macOS: brew install postgresql\n"
            "• Debian/Ubuntu: sudo apt-get install postgresql-client\n"
            "• Windows: install via Postgres installer or WSL\n",
            title="Missing pg_dump", box=box.ROUNDED, style="red"
        ))
        sys.exit(1)

def gather_connection_url():
    console.rule("[bold blue]Step 2: Database URI[/]")
    console.print(
        "1) In your Supabase project, click the \"Connect\" button on the top navbar\n"
        "2) Under the \"Connection String\" tab, copy the Transaction Pooler URI in this exact format (when you copy the string from Supabase it will already include the <PROJECT> part),\n\n"
        "   postgresql://postgres.<PROJECT>:[YOUR-PASSWORD]@"
        "aws-0-us-east-2.pooler.supabase.com:6543/postgres\n"
    )
    env_url = os.getenv("SUPABASE_DB_URL")
    if env_url:
        console.print("[green]Using SUPABASE_DB_URL from environment[/]\n")
        return env_url

    uri_template = Prompt.ask(
        "Paste the Pooler URI with [YOUR-PASSWORD] placeholder",
        show_default=False
    )
    expected_prefix = "postgresql://postgres."
    expected_suffix = "@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    if not uri_template.startswith(expected_prefix) \
       or "[YOUR-PASSWORD]" not in uri_template \
       or not uri_template.endswith(expected_suffix):
        console.print("[red]Invalid format! Make sure it matches exactly:[/]")
        console.print(f"  {expected_prefix}[YOUR-PASSWORD]{expected_suffix}")
        return gather_connection_url()

    pwd = Prompt.ask("Enter your database password", password=True)
    full_url = uri_template.replace("[YOUR-PASSWORD]", pwd)
    console.print("[green]🔑 Password inserted into URI[/]\n")
    return full_url


def choose_output_dir():
    console.rule("[bold blue]Step 3: Output Directory[/]")
    env_dir = os.getenv("BACKUP_DIR")
    if env_dir:
        if os.path.isdir(env_dir):
            console.print(f"[green]Using BACKUP_DIR: {env_dir}[/]\n")
            return env_dir
        console.print(f"[red]Error: BACKUP_DIR '{env_dir}' is not a directory[/]")
        sys.exit(1)
    path = Prompt.ask("Directory to save backup", default=os.getcwd())
    if not os.path.isdir(path):
        console.print(f"[red]'{path}' is not a directory[/]")
        return choose_output_dir()
    return path

def run_backup(db_url, out_dir, overwrite):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (os.path.join(out_dir, "supabase_backup.dump")
                if overwrite else
                os.path.join(out_dir, f"supabase_backup_{now}.dump"))
    cmd = ["pg_dump", db_url, "--format", "custom", "--file", filename]
    console.print(Panel(Text.assemble(("Backing up to ", "green"), (filename, "bold white")),
                        title="Starting Backup", box=box.ROUNDED, style="cyan"))
    try:
        with console.status("[bold blue]Running pg_dump…[/]", spinner="dots"):
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        console.print(Panel(Text.assemble(
            ("pg_dump failed (code ", "red"), (str(e.returncode), "bold"),
            (")\n\nStderr:\n", "red"), (e.stderr.decode(), "white")),
            title="Backup Error", box=box.ROUNDED, style="red"))
        sys.exit(1)
    console.print(Panel(Text.assemble(("✅ Backup saved to\n", "green"), (filename, "bold white")),
                        title="Done", box=box.ROUNDED, style="green"))

def install_cron_job(db_url, out_dir, overwrite, interval):
    console.rule("[bold blue]Step 5: Install Cron Job[/]")
    minute = datetime.now().minute
    console.print(
        f"Scheduling backups every {interval} hour(s) at minute {minute}."
    )
    cron_cmd = (
        f"{minute} */{interval} * * * "
        f"SUPABASE_DB_URL='{db_url}' BACKUP_DIR='{out_dir}' "
        f"OVERWRITE={'true' if overwrite else 'false'} INTERVAL_HOURS={interval} "
        f"/usr/bin/env python3 {SCRIPT_PATH} "
        f">> {os.path.join(out_dir,'backup.log')} 2>&1"
    )

    # Read current crontab (if any)
    try:
        raw = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode().splitlines()
    except subprocess.CalledProcessError:
        raw = []

    # Remove any previous entries for this script
    filtered = [line for line in raw if SCRIPT_PATH not in line]

    # Append the new cron entry
    filtered.append(cron_cmd)
    new_cron = "\n".join(filtered) + "\n"

    # Install the updated crontab
    p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    p.communicate(new_cron.encode())

    console.print(
        Panel(cron_cmd, title="Cron entry installed (replaced previous)", box=box.ROUNDED, style="magenta")
    )
    console.print(f"[green]Your database will now be backed up every {interval} hour(s).[/]")
    console.print(f"[yellow]To cancel this schedule, run:[/] python3 {SCRIPT_PATH} --remove-cron")

def main():
    # handle removal flag
    if "--remove-cron" in sys.argv:
        remove_cron_job()

    print_intro()
    check_pg_dump()

    console.rule("[bold blue]Step 1: Overwrite Mode[/]")
    console.print(
        "Overwrite the same file each run (supabase_backup.dump)?\n"
        "Otherwise, create a new timestamped file."
    )
    overwrite = Confirm.ask("Overwrite each run?", default=False)

    db_url = gather_connection_url()
    out_dir = choose_output_dir()

    console.rule("[bold blue]Step 4: One-Time Backup[/]")
    run_backup(db_url, out_dir, overwrite)

    if Confirm.ask("Install a cron job for recurring backups?", default=False):
        interval = Prompt.ask("Interval in hours", default="24")
        try:
            iv = int(interval)
        except ValueError:
            console.print("[red]Please enter a valid integer[/]")
            sys.exit(1)
        install_cron_job(db_url, out_dir, overwrite, iv)
    else:
        console.print("[green]Finished without scheduling[/]")

if __name__ == "__main__":
    main()