from flask import current_app
from flask_mailman import EmailMessage
from flask import render_template
from flask_mailman import EmailMessage
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from ..utils.decorators import with_app_context

mail_executors = ThreadPoolExecutor(max_workers=25)

@with_app_context
def mail_worker_task(app, to_email:str, subject:str, template:str, **kwargs):
        try:
            html_content = render_template(template, **kwargs)
            msg = EmailMessage(subject=subject, body="This is a fallback text.", to=[to_email])
            msg.html = html_content
            msg.send()
        except Exception as e:
            app.logger.error(f"Failed to send email to {to_email}: {str(e)}")

def send_email_async(to_email:str, subject:str, template:str, **kwargs):
    true_app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
    mail_executors.submit(mail_worker_task, true_app, to_email, subject, template, **kwargs)

def send_welcome_email(to_email: str, info: dict):
    subject = "🚀 Welcome to Uptime Sentinel!"
    template = 'emails/welcome_email.html'
    send_email_async(to_email, subject, template, email=to_email, info=info)

def send_tracking_update_email(to_email: str, info: dict):
    subject = "🔄 Uptime Sentinel: Monitoring Profile Updated"
    template = 'emails/tracking_update.html'
    send_email_async(to_email, subject, template, email=to_email, info=info)

def send_alert_email(to_email: str, target_url: str, event_time: datetime, is_recovery: bool = False):
    # 🚀 Dynamic Content Switching
    meta = {
    True: ("✅", "Back Online!"),
    False: ("⚠️ Uptime Sentinel Alert:", "Downtime Detected for")
}
    emoji, text = meta[is_recovery]
    subject = f"{emoji} Uptime Sentinel: {target_url} is {text}" if is_recovery else f"{emoji} {text} {target_url}"
    
    template = 'emails/alert_email.html'
    send_email_async(to_email, subject, template, email=to_email, target_url=target_url, event_time=event_time.strftime("%Y-%m-%d %H:%M:%S"), is_recovery=is_recovery)

def send_daily_report_email(to_email: str, report_data: list):
    subject = "📊 Your Daily Uptime Sentinel Status Report for {{ date }}".format(date=datetime.utcnow().strftime("%Y-%m-%d"))
    template = 'emails/daily_report.html'   
    send_email_async(to_email, subject, template, data=report_data)
