from twentyfivefirst.celery import app as celery_app
from celery import Task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
from django.core.cache import cache
# [SECURITY] Image processing imports hidden for safety

logger = logging.getLogger(__name__)

# [SECURITY] Cache Configuration
EMAIL_IDEMPOTENCY_TTL = 60 * 60 * 24
LOGO_CACHE_KEY = "email_logo_binary_data"

class BaseEmailTask(Task):
    """
    Abstract base task that handles error reporting and automatic retries
    with exponential backoff.
    """
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    max_retries = 5
    time_limit = getattr(settings, "CELERY_TASK_SOFT_TIME_LIMIT", 300)

@celery_app.task(bind=True, base=BaseEmailTask, name="mainapp.tasks.email.send_email_task")
def send_email_task(self, subject, plain_text, html_content, recipient_list, from_email=None, idempotency_key=None):
    """
    Asynchronously sends transactional emails.
    
    Features:
    1. Idempotency: Prevents double-sending if the task is re-queued.
    2. Asset Optimization: Caches the logo binary in Redis to reduce disk I/O on high volume.
    3. Failure Recovery: Automatically retries on SMTP errors.
    """
    try:
        # ------------------------------------------------------------------
        # 1. IDEMPOTENCY CHECK
        # ------------------------------------------------------------------
        if idempotency_key:
            if cache.get(f"email_sent:{idempotency_key}"):
                logger.info("Email with idempotency_key %s already sent — skipping", idempotency_key)
                return {"skipped": True}

        # ------------------------------------------------------------------
        # 2. MESSAGE CONSTRUCTION & ASSET EMBEDDING
        # ------------------------------------------------------------------
        # [SECURITY] Implementation Hidden
        # This block contains logic to:
        # - Initialize EmailMultiAlternatives.
        # - Detect 'cid:logo_image' in HTML.
        # - Fetch logo from Redis (or disk on cache miss).
        # - Attach logo as a MIMEImage with correct headers for inline display.

        # ------------------------------------------------------------------
        # 3. DISPATCH & STATE UPDATE
        # ------------------------------------------------------------------
        # [SECURITY] SMTP Send Logic Hidden
        # msg.send(fail_silently=False)

        if idempotency_key:
            cache.set(f"email_sent:{idempotency_key}", "1", timeout=EMAIL_IDEMPOTENCY_TTL)

        # [SECURITY] PII removed from logs
        logger.info("Sent email '%s' to %s recipients", subject, len(recipient_list))
        return {"sent": True}

    except Exception as exc:
        logger.exception("send_email_task failed.")
        # Celery will automatically retry based on BaseEmailTask settings
        raise