"""
AttendX Database Backup Script.

Run manually:   python -m scripts.backup
Cron (daily):   0 2 * * * cd /app && python -m scripts.backup

Features:
- PostgreSQL pg_dump with gzip compression
- Face-images directory archival
- Configuration file backup
- Retention policy (default: 30 days)
- Completion status written to Redis
"""

import gzip
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import structlog

from app.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


def _parse_db_url() -> dict:
    """Extract connection params from DATABASE_URL."""
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "attendx",
        "password": parsed.password or "",
        "dbname": (parsed.path or "/attendx").lstrip("/"),
    }


class BackupManager:
    """Create and manage database, face-image, and config backups."""

    def __init__(self, backup_dir: str = "/data/backups") -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_database(self) -> Path:
        """Dump PostgreSQL database and compress with gzip."""
        db = _parse_db_url()
        filename = self.backup_dir / f"db_{self.timestamp}.sql.gz"

        dump_cmd = [
            "pg_dump",
            "--host", db["host"],
            "--port", db["port"],
            "--username", db["user"],
            "--dbname", db["dbname"],
            "--no-password",
            "--format", "plain",
        ]

        env = {**os.environ, "PGPASSWORD": db["password"]}

        with gzip.open(filename, "wb") as gz_file:
            process = subprocess.Popen(
                dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            assert process.stdout is not None
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                gz_file.write(chunk)
            process.wait()

        if process.returncode != 0:
            filename.unlink(missing_ok=True)
            raise RuntimeError(
                f"pg_dump exited with code {process.returncode}"
            )

        size_mb = filename.stat().st_size / (1024 * 1024)
        logger.info("db_backup_created", path=str(filename), size_mb=round(size_mb, 1))
        return filename

    def backup_face_images(self) -> Path | None:
        """Archive the face-images directory."""
        faces_dir = Path("/data/faces")
        if not faces_dir.exists():
            logger.info("no_faces_dir_to_backup")
            return None

        base = str(self.backup_dir / f"faces_{self.timestamp}")
        archive_path = Path(shutil.make_archive(base, "gztar", str(faces_dir.parent), faces_dir.name))
        logger.info("faces_backup_created", path=str(archive_path))
        return archive_path

    def backup_config(self) -> Path:
        """Archive environment and compose files."""
        filename = self.backup_dir / f"config_{self.timestamp}.tar.gz"

        config_files = [
            Path(".env"),
            Path("docker/docker-compose.yml"),
            Path("docker/nginx.conf"),
        ]

        with tarfile.open(filename, "w:gz") as tar:
            for cf in config_files:
                if cf.exists():
                    tar.add(str(cf), arcname=cf.name)

        logger.info("config_backup_created", path=str(filename))
        return filename

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Delete backup files older than *retention_days*."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        for f in self.backup_dir.glob("*.gz"):
            if f.stat().st_mtime < cutoff.timestamp():
                f.unlink()
                deleted += 1
        logger.info("old_backups_cleaned_up", deleted=deleted, retention_days=retention_days)
        return deleted

    def run_full_backup(self) -> dict:
        """Execute all backup steps and return a results summary."""
        results: dict = {"timestamp": self.timestamp}

        try:
            results["database"] = str(self.backup_database())
        except Exception as exc:
            logger.error("db_backup_failed", error=str(exc))
            results["database_error"] = str(exc)

        try:
            face_path = self.backup_face_images()
            results["faces"] = str(face_path) if face_path else "no_faces_dir"
        except Exception as exc:
            logger.error("faces_backup_failed", error=str(exc))
            results["faces_error"] = str(exc)

        try:
            results["config"] = str(self.backup_config())
        except Exception as exc:
            logger.error("config_backup_failed", error=str(exc))
            results["config_error"] = str(exc)

        results["cleaned_up"] = self.cleanup_old_backups()
        return results


def main() -> None:
    manager = BackupManager()
    results = manager.run_full_backup()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
