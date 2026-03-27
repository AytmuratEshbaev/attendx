# AttendX Production Security Checklist

## Before Deployment

- [ ] Change all default passwords (admin, database, Redis)
- [ ] Generate strong `SECRET_KEY` (64 chars random):
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- [ ] Generate strong `JWT_SECRET` (32 chars random):
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Generate Fernet key:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] Set `LOG_LEVEL=INFO` (not `DEBUG`)
- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Set `ALLOWED_ORIGINS` to the actual frontend domain only
- [ ] Enable HTTPS (SSL certificate via Let's Encrypt / Certbot)
- [ ] Set `TELEGRAM_BOT_TOKEN` to the real bot token
- [ ] Set `ADMIN_CHAT_ID` for Telegram admin alerts
- [ ] Configure `SENTRY_DSN` for error tracking (optional)

---

## Firewall (ufw)

```bash
ufw default deny incoming
ufw allow 80/tcp     # HTTP → nginx redirects to HTTPS
ufw allow 443/tcp    # HTTPS
ufw allow 22/tcp     # SSH — restrict to admin IP if possible
ufw deny 5432/tcp    # PostgreSQL — internal Docker network only
ufw deny 6379/tcp    # Redis — internal Docker network only
ufw enable
```

---

## Database

- [ ] PostgreSQL: set `sslmode=require` in `DATABASE_URL`
- [ ] Change the default `postgres` superuser password
- [ ] Create a **dedicated** DB user with only the permissions AttendX needs
  (no `SUPERUSER`, no `CREATEDB`)
- [ ] Restrict `pg_hba.conf` to local connections only
- [ ] Enable WAL archiving for point-in-time recovery (production)

---

## Redis

- [ ] Set a strong Redis `requirepass` in `redis.conf`
- [ ] Bind Redis to `127.0.0.1` or the Docker internal network only
- [ ] Disable dangerous commands: `rename-command FLUSHALL ""`

---

## API Keys

- [ ] Rotate the `DEFAULT_API_KEY` immediately after first deployment
- [ ] Never log raw API keys — only key previews (`atx_****xxxx`)
- [ ] Rotate API keys every **90 days** (use `POST /api/v1/api-keys/{id}/rotate`)
- [ ] Revoke any unused API keys (`DELETE /api/v1/api-keys/{id}`)

---

## Monitoring

- [ ] `SENTRY_DSN` configured and verified
- [ ] Backup cron job running (daily at 2 AM):
  ```cron
  0 2 * * * cd /app && python -m scripts.backup >> /var/log/attendx_backup.log 2>&1
  ```
- [ ] Health check monitoring via uptime robot, Better Stack, or similar
  - Endpoint: `GET /health`
  - Expected: `{"status": "ok"}`
- [ ] Admin Telegram alerts configured (`ADMIN_CHAT_ID`)
- [ ] Review `GET /health/detailed` regularly (worker heartbeat, disk space)

---

## Regular Maintenance

| Task | Frequency |
|------|-----------|
| Rotate API keys | Every 90 days |
| Review audit logs (`GET /api/v1/audit-logs`) | Weekly |
| Check blocked IPs (`GET /api/v1/security/blocked-ips`) | Weekly |
| Update Python dependencies | Monthly (`poetry update`) |
| Test backup restore | Quarterly |
| Rotate `JWT_SECRET` (requires re-login for all users) | Annually or after incident |
| Review ALLOWED_ORIGINS | After frontend domain changes |

---

## Nginx TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_timeout 1d;
    ssl_session_cache   shared:SSL:10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://attendx-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

---

## Incident Response

If a breach is suspected:

1. **Revoke all sessions**: `POST /api/v1/security/revoke-all-sessions`
2. **Rotate JWT_SECRET** in `.env` and restart all services
3. **Revoke all API keys** and issue new ones
4. **Review audit logs** for the last 7 days
5. **Check blocked IPs** for unusual patterns
6. **Notify affected users** if personal data may have been exposed
7. **File incident report** in the team's incident tracker
