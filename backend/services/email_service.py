import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from backend.config.settings import settings

logger = logging.getLogger("email_service")


class EmailAlertService:
    """
    Law Enforcement Email Dispatcher for Monitored Cryptocurrency Wallets.
    Sends automated intelligence notices to investigators when new transactions,
    balance shifts, or VASP deposit hops are detected.
    """

    @staticmethod
    def send_wallet_activity_alert(
        target_address: str,
        chain: str,
        alert_type: str,
        description: str,
        tx_hash: Optional[str] = None,
        recipient_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Constructs and transmits an official Law Enforcement Email Alert.
        Gracefully handles unconfigured SMTP settings with informative fallback logs.
        """
        recipient = recipient_email or settings.ALERT_EMAIL_RECIPIENT
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            logger.info(f"Email alerts disabled in settings. Skipping email dispatch for {target_address}.")
            return {
                "sent": False,
                "reason": "Email alerts toggle disabled in settings",
                "recipient": recipient,
            }

        if not settings.SMTP_HOST or not recipient:
            logger.info(f"SMTP host or recipient unconfigured. Alert logged internally for {target_address}.")
            return {
                "sent": False,
                "reason": "SMTP host or recipient unconfigured in settings",
                "recipient": recipient,
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[LEA ALERT - I4C/SAHYOG] New Activity on Monitored Wallet: {target_address[:10]}..."
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = recipient

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px;">
                    <div style="border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px;">
                        <h2 style="color: #38bdf8; margin: 0; font-size: 20px;">INDIAN CYBER CRIME COORDINATION CENTRE (I4C)</h2>
                        <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 12px;">SAHYOG Automated Blockchain Intelligence Alert</p>
                    </div>

                    <div style="background-color: #0f172a; border-left: 4px solid #ef4444; padding: 12px 16px; margin-bottom: 20px;">
                        <span style="color: #ef4444; font-weight: bold; font-size: 14px;">ALERT TRIGGER: {alert_type.upper()}</span>
                        <p style="color: #cbd5e1; margin: 6px 0 0 0; font-size: 13px;">{description}</p>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Target Wallet:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #334155; color: #f1f5f9; font-family: monospace;">{target_address}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Blockchain:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #334155; color: #f1f5f9; text-transform: uppercase;">{chain}</td>
                        </tr>
                        {f'<tr><td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Transaction Hash:</td><td style="padding: 8px; border-bottom: 1px solid #334155; color: #38bdf8; font-family: monospace;">{tx_hash}</td></tr>' if tx_hash else ''}
                    </table>

                    <div style="border-top: 1px solid #334155; padding-top: 16px; text-align: center;">
                        <a href="http://localhost:3001" style="background-color: #0284c7; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block;">
                            Open SAHYOG Forensic Workstation
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [recipient], msg.as_string())

            logger.info(f"Successfully dispatched alert email to {recipient} for {target_address}")
            return {"sent": True, "recipient": recipient}
        except Exception as e:
            logger.warning(f"Failed to send email alert via SMTP: {e}")
            return {"sent": False, "reason": str(e), "recipient": recipient}


email_service = EmailAlertService()
