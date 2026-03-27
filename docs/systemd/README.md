# AttendX Systemd Service Files

These service files allow running AttendX services natively on a Linux server
(without relying on `restart: always` in Docker Compose).

## Installation

```bash
# Copy service files to systemd
sudo cp docs/systemd/*.service docs/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start all services
sudo systemctl enable --now attendx-backend
sudo systemctl enable --now attendx-worker
sudo systemctl enable --now attendx-bot
sudo systemctl enable --now attendx-backup.timer
```

## Service Management

```bash
# Check status
sudo systemctl status attendx-backend
sudo systemctl status attendx-worker
sudo systemctl status attendx-bot
sudo systemctl status attendx-backup.timer

# View logs
sudo journalctl -u attendx-backend -f
sudo journalctl -u attendx-worker -f

# Backup logs
cat /var/log/attendx_backup.log
```

## Notes

- Services expect project to be installed at `/opt/attendx`
- The backup timer runs daily at 02:00 AM
- All services restart automatically on failure (with 10–15s delay)
