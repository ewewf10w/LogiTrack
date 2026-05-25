import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from aiosmtplib import send
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email_async(to_email: str, subject: str, html_content: str):
    message = MIMEMultipart()
    message["From"] = settings.smtp.from_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        is_ssl_port = True if settings.smtp.port == 465 else False

        await send(
            message,
            hostname=settings.smtp.host,
            port=settings.smtp.port,
            username=settings.smtp.user,
            password=settings.smtp.password,
            use_tls=is_ssl_port,
        )
        print(f"\n[УСПЕХ] Письмо отправлено на {to_email}!\n")

    except Exception as e:
        logger.error(f"Ошибка при отправке Email на {to_email}: {e}")
        print(f"\n[ОШИБКА SMTP]: {e}\n")
