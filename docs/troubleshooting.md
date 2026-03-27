# Troubleshooting

## Common Issues

### Database connection refused

**Symptom:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Fix:** Ensure PostgreSQL is running:
```bash
docker compose -f docker/docker-compose.yml up -d db
```

Check the `DATABASE_URL` in your `.env` matches the Docker service configuration.

### Redis connection error

**Symptom:** `redis.exceptions.ConnectionError`

**Fix:** Ensure Redis is running:
```bash
docker compose -f docker/docker-compose.yml up -d redis
```

### Frontend build fails

**Symptom:** `pnpm install` or `pnpm build` fails

**Fix:**
```bash
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Alembic migration errors

**Symptom:** `alembic upgrade head` fails

**Fix:**
1. Ensure the database is running and accessible
2. Check `DATABASE_URL` in `.env`
3. If starting fresh: `docker compose -f docker/docker-compose.yml down -v` and restart

### Port conflicts

**Symptom:** `Address already in use`

**Fix:** Check what's using the port and stop it:
```bash
# Linux/Mac
lsof -i :8000
# Windows
netstat -ano | findstr :8000
```

### CORS errors in browser

**Symptom:** `Access-Control-Allow-Origin` errors in browser console

**Fix:** Ensure your frontend URL is in the `CORS_ORIGINS` setting in `.env` or `config.py`.
