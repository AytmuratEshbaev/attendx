#!/bin/bash
# ==============================================================================
# AttendX — SSL Certificate Setup with Let's Encrypt (Certbot)
# ==============================================================================
# Usage: bash docker/setup-ssl.sh your-domain.com admin@your-domain.com
# ==============================================================================

set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 attendx.example.com admin@example.com"
    exit 1
fi

echo "==> Setting up SSL for domain: $DOMAIN"
echo "==> Contact email: $EMAIL"

# -- 1. Install certbot if missing -------------------------------------------
if ! command -v certbot &>/dev/null; then
    echo "==> Installing certbot..."
    apt-get update -qq
    apt-get install -y certbot python3-certbot-nginx
fi

# -- 2. Ensure nginx is serving HTTP (for ACME challenge) --------------------
echo "==> Starting nginx for ACME challenge..."
docker compose -f docker/docker-compose.prod.yml up -d nginx || true
sleep 3

# -- 3. Obtain certificate ---------------------------------------------------
echo "==> Obtaining Let's Encrypt certificate..."
certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domain "$DOMAIN" \
    --deploy-hook "docker compose -f docker/docker-compose.prod.yml exec nginx nginx -s reload"

echo "==> Certificate obtained successfully!"
echo ""

# -- 4. Update nginx.conf with domain ----------------------------------------
echo "==> Updating nginx.conf with domain: $DOMAIN"
export DOMAIN
envsubst '${DOMAIN}' < docker/nginx.conf > /tmp/nginx_rendered.conf
cp /tmp/nginx_rendered.conf docker/nginx.conf.rendered
echo "    Rendered config saved to docker/nginx.conf.rendered"
echo "    Review and copy to docker/nginx.conf if correct."
echo ""

# -- 5. Set up auto-renewal cron ---------------------------------------------
CRON_JOB="0 3 * * * certbot renew --quiet --deploy-hook 'docker compose -f $(pwd)/docker/docker-compose.prod.yml exec nginx nginx -s reload'"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "==> Auto-renewal cron job added (daily at 3 AM)"

echo ""
echo "===================================================================="
echo "SSL setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review docker/nginx.conf — replace \${DOMAIN} with: $DOMAIN"
echo "  2. Restart nginx: docker compose -f docker/docker-compose.prod.yml restart nginx"
echo "  3. Verify: https://$DOMAIN/health"
echo "===================================================================="
