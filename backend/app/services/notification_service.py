import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_alert_email(unit_name: str, parameter_name: str, severity: str, message: str, breach_info: str = ""):
        """
        Sends email notification for WARNING and CRITICAL alerts if EMAIL_ALERTS_ENABLED is true.
        Never throws unhandled exceptions; logs failure cleanly.
        """
        enabled = current_app.config.get('EMAIL_ALERTS_ENABLED', False)
        if not enabled:
            logger.info(f"[EMAIL NOTIFICATION DISABLED] Alert for {unit_name} - {parameter_name} ({severity}): {message}")
            return False

        smtp_host = current_app.config.get('SMTP_HOST')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_user = current_app.config.get('SMTP_USERNAME')
        smtp_pass = current_app.config.get('SMTP_PASSWORD')
        email_from = current_app.config.get('ALERT_EMAIL_FROM')
        email_to = current_app.config.get('ALERT_EMAIL_TO')

        if not smtp_host or not email_from or not email_to:
            logger.warning("SMTP configuration incomplete. Cannot send email alert.")
            return False

        subject = f"[{severity}] Turbine Predictive Alert: {unit_name} - {parameter_name}"
        body = f"""
INDUSTRIAL TURBINE PREDICTIVE MONITORING SYSTEM
==============================================
Severity: {severity}
Turbine: {unit_name}
Parameter: {parameter_name}
Message: {message}
{breach_info}

Please inspect SCADA Control Room Console immediately.
"""
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Alert email sent successfully to {email_to} for {unit_name} {parameter_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
