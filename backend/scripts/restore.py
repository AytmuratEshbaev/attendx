"""
AttendX Database Restore Script.

Usage:
    python -m scripts.restore --file /data/backups/db_20260219_020000.sql.gz

WARNING: This will DROP all existing data in the target database.
         Only run this in a controlled environment with explicit confirmation.
"""

import argparse
import gzip
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import structlog

from app.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


def _parse_db_url() -> dict:
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "attendx",
        "password": parsed.password or "",
        "dbname": (parsed.path or "/attendx").lstrip("/"),
    }


def restore_database(backup_file: Path) -> None:
    """
    Restore a PostgreSQL database from a gzip-compressed SQL dump.

    Steps:
    1. Drop and recreate the database.
    2. Pipe the decompressed dump through psql.
    """
    if not backup_file.exists():
        logger.error("backup_file_not_found", path=str(backup_file))
        sys.exit(1)

    db = _parse_db_url()
    env = {**os.environ, "PGPASSWORD": db["password"]}

    logger.info(
        "restore_starting",
        file=str(backup_file),
        database=db["dbname"],
    )

    # Confirm with the user
    answer = input(
        f"\n⚠️  This will OVERWRITE all data in '{db['dbname']}' on {db['host']}.\n"
        "Type 'yes' to confirm: "
    )
    if answer.strip().lower() != "yes":
        print("Restore cancelled.")
        sys.exit(0)

    psql_cmd = [
        "psql",
        "--host", db["host"],
        "--port", db["port"],
        "--username", db["user"],
        "--dbname", db["dbname"],
        "--no-password",
    ]

    with gzip.open(backup_file, "rb") as gz_file:
        process = subprocess.Popen(
            psql_cmd,
            stdin=gz_file,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = process.communicate()

    if process.returncode != 0:
        logger.error(
            "restore_failed",
            returncode=process.returncode,
            stderr=stderr.decode()[:500],
        )
        sys.exit(1)

    logger.info("restore_completed", file=str(backup_file))
    print(f"✅  Restore complete from {backup_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore AttendX database from backup")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the .sql.gz backup file",
    )
    args = parser.parse_args()
    restore_database(Path(args.file))


if __name__ == "__main__":
    main()
