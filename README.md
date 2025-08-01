# Supabase Postgres Backup Script

A lightweight Python script to back up your Supabase Postgres database—one-time or on a recurring schedule.

---


## Requirements

- **Python 3.8+** (recommended 3.10+)
- **pg_dump** (PostgreSQL client tool)
- **pip** (Python package installer)
- Access to your Supabase project's [Transaction Pooler] database URL

---

## Quickstart

Clone this repo and run the setup script:

```bash
git clone https://github.com/DuncBoi/SupabaseBackupScript.git
cd SupabaseBackupScript
bash setup.sh
```

Activate your environment and run the backup script:

```bash
source .venv/bin/activate
python supabase_backup.py
```

The script will guide you:

* Where to get your Supabase "Transaction Pooler" database URL
* Where to save the backup
* How to schedule recurring backups
* How to overwrite or keep separate backups

---

## Scheduling (Recurring Backups)

If you choose to schedule, the script will generate a cron job for you and explain how to use/remove it.
You can view or edit scheduled jobs at any time:

```bash
crontab -e
```

To remove the scheduled backup, simply delete the backup line from your `crontab` file.

---

## Uninstall

To remove your virtual environment and backup files:

```bash
deactivate  # (if you're in the venv)
rm -rf .venv supabase_backup_*.dump
```

---

## Troubleshooting

* Make sure `pg_dump` is installed and in your PATH.

  * On macOS: `brew install postgresql`
  * On Ubuntu/Debian: `sudo apt-get install postgresql-client`
  * On Windows: Install from [postgresql.org](https://www.postgresql.org/download/windows/)
* If you get connection errors, double-check your Supabase database URL and password.
* If cron jobs don't run as expected, make sure your machine is on and not asleep at the scheduled time.

---

## About

Built with [rich](https://github.com/Textualize/rich) for terminal UI.

**Author:** Duncan Greene
