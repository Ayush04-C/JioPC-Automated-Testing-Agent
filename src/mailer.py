import smtplib
from email.message import EmailMessage
import os
from typing import Dict, Any

def send_summary_email(config: Dict[str, Any], analysis_result: str) -> None:
    """Sends the LLM analysis result via email if configured."""
    email_config = config.get("agent", {}).get("email", {})
    if not email_config.get("enabled", False):
        return

    smtp_server = email_config.get("smtp_server")
    smtp_port = email_config.get("smtp_port", 587)
    smtp_user = email_config.get("smtp_user")
    to_address = email_config.get("to_address")
    from_address = email_config.get("from_address")
    
    # Securely read password from environment
    smtp_pass = os.getenv("SMTP_PASS")
    
    if not all([smtp_server, smtp_user, to_address, from_address, smtp_pass]):
        print("Warning: Email is enabled but SMTP configuration or SMTP_PASS environment variable is incomplete. Skipping email.")
        return

    msg = EmailMessage()
    msg.set_content(analysis_result)
    msg['Subject'] = 'JioPC Testing Agent - Validation Report'
    msg['From'] = from_address
    msg['To'] = to_address

    try:
        print(f"\nSending summary email to {to_address}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
