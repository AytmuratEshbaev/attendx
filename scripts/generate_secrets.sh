#!/bin/bash
# ==============================================================================
# AttendX — Maktab serveri uchun kuchli secretlarni avtomatik generate qilish
# Ishlatish: bash scripts/generate_secrets.sh
# Natijani .env.school fayliga ko'chiring
# ==============================================================================

set -e

echo ""
echo "AttendX Secret Generator"
echo "========================"
echo ""

python3 - <<'EOF'
import secrets
import sys

try:
    from cryptography.fernet import Fernet
    fernet_key = Fernet.generate_key().decode()
except ImportError:
    fernet_key = "Run: pip install cryptography"

print("# Quyidagi qiymatlarni .env.school fayliga ko'chiring:")
print()
print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
print(f"JWT_SECRET={secrets.token_urlsafe(32)}")
print(f"FERNET_KEY={fernet_key}")
print(f"POSTGRES_PASSWORD={secrets.token_hex(24)}")
print(f"REDIS_PASSWORD={secrets.token_hex(24)}")
print(f"DEFAULT_API_KEY={secrets.token_urlsafe(32)}")
print()
print("# POSTGRES_PASSWORD va REDIS_PASSWORD ni .env.school da 3 joyda almashtiring:")
print("# - POSTGRES_PASSWORD=")
print("# - DATABASE_URL ichida (attendx:CHANGE_ME_STRONG_PW@db)")
print("# - DATABASE_URL_SYNC ichida")
print("# - REDIS_URL ichida (:CHANGE_ME_REDIS_PW@redis)")
print("# - REDIS_PASSWORD=")
EOF
