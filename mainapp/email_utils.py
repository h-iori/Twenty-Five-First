import textwrap
from datetime import datetime
from pathlib import Path
from email.mime.image import MIMEImage
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction

logger = logging.getLogger(__name__)

def _local_logo_path():
    """
    [SECURITY] File System Logic Hidden
    Resolves the absolute path to the brand logo for CID embedding.
    """
    return None

def _default_logo_src():
    return "cid:logo_image"

def html_email_wrapper(subject, preheader, body_html, logo_src=None):
    """
    [SECURITY] Enterprise Email Template Hidden
    
    Wraps the content in a responsive HTML skeleton.
    Features hidden:
    1. Inline CSS for maximum client compatibility (Gmail, Outlook).
    2. Mobile-responsive container queries.
    3. Standardized Header/Footer branding.
    """
    return textwrap.dedent(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
      <style>
        /* [SECURITY] Corporate Identity Styles Hidden */
      </style>
    </head>
    <body>
      <span class="preheader">{preheader}</span>
      <div class="email-wrapper">
        <div class="email-container">
          <div class="header">
             </div>
          
          <div class="content">
            {body_html}
          </div>
          
          <div class="footer">
            <div class="muted">© {datetime.utcnow().year} Project Name. All rights reserved.</div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """)

def send_html_email(subject, plain_text, html_content, recipient_list, from_email=None, fail_silently=True):
    """
    [SECURITY] SMTP Dispatch Logic Hidden
    
    Constructs a MIME Multipart message:
    1. Attaches the Plain Text version (for anti-spam scores).
    2. Attaches the HTML version.
    3. Detects 'cid:' references and embeds local images as MIME attachments 
       to prevent email clients from blocking remote images.
    """
    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    
    msg = EmailMultiAlternatives(subject=subject, body=plain_text, from_email=from_email, to=recipient_list)
    msg.attach_alternative(html_content, "text/html")

    # [SECURITY] MIME Image Embedding Logic
    if "cid:logo_image" in html_content:
        # Logic to read binary file and attach as Content-ID hidden
        pass
    
    try:
        msg.send(fail_silently=fail_silently)
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {e}")
        if not fail_silently:
            raise

def send_html_email_async(subject, plain_text, html_content, recipient_list, from_email=None, idempotency_key=None):
    """
    [SECURITY] Async Task Dispatch Hidden
    
    Offloads email sending to a Celery worker queue ('emails').
    
    Crucial Architecture Detail:
    Uses `transaction.on_commit` to ensure the task is ONLY enqueued after 
    the current database transaction successfully commits. This prevents race conditions 
    where the worker tries to process data that hasn't been saved yet.
    """
    def _enqueue():
        # Import task dynamically to avoid circular imports
        from mainapp.tasks.email import send_email_task
        
        send_email_task.apply_async(
            args=[subject, plain_text, html_content, recipient_list, from_email, idempotency_key],
            queue="emails"
        )
    
    try:
        transaction.on_commit(_enqueue)
    except Exception:
        # Fallback if not inside a transaction
        _enqueue()