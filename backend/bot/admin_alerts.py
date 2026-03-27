"""Admin alert notifications via Telegram."""

from datetime import datetime

import structlog
from telegram import Bot

logger = structlog.get_logger()


class AdminAlerter:
    """Send critical system alerts to admin Telegram channel/group."""

    def __init__(self, bot: Bot, admin_chat_id: int) -> None:
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    async def _send(self, text: str) -> None:
        """Send a message to admin chat, logging errors instead of raising."""
        if not self.admin_chat_id:
            return
        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error("admin_alert_failed", error=str(e))

    async def device_offline_alert(self, device_name: str, ip: str) -> None:
        await self._send(
            f"🔴 <b>Terminal oflayn!</b>\n\n"
            f"📡 {device_name}\n"
            f"🌐 {ip}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )

    async def device_online_alert(self, device_name: str, ip: str) -> None:
        await self._send(
            f"🟢 <b>Terminal onlayn!</b>\n\n"
            f"📡 {device_name}\n"
            f"🌐 {ip}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )

    async def error_alert(self, error_type: str, details: str) -> None:
        await self._send(
            f"⚠️ <b>Xatolik!</b>\n\n"
            f"Turi: {error_type}\n"
            f"Tafsilot: {details[:500]}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )

    async def daily_summary(self, stats: dict) -> None:
        await self._send(
            f"📊 <b>Kunlik hisobot</b>\n\n"
            f"👥 Jami: {stats['total']}\n"
            f"✅ Keldi: {stats['present']}\n"
            f"❌ Kelmadi: {stats['absent']}\n"
            f"📈 Foiz: {stats['percentage']:.1f}%\n"
            f"📡 Terminallar: {stats['devices_online']}/{stats['devices_total']}"
        )
