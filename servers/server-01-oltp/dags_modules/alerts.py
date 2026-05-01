"""
Уведомления (Telegram, Slack)
"""
import logging
import requests
from airflow.models import Variable

logger = logging.getLogger(__name__)

def send_telegram_alert(message, chat_id=None, bot_token=None):
    """Отправка уведомления в Telegram"""
    chat_id = chat_id or Variable.get('TELEGRAM_CHAT_ID', default_var=None)
    bot_token = bot_token or Variable.get('TELEGRAM_BOT_TOKEN', default_var=None)
    
    if not chat_id or not bot_token:
        logger.warning("Telegram не настроен: отсутствуют TELEGRAM_CHAT_ID или TELEGRAM_BOT_TOKEN")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Telegram уведомление отправлено")
            return True
        else:
            logger.error(f"❌ Ошибка Telegram: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def send_slack_alert(message, webhook_url=None):
    """Отправка уведомления в Slack"""
    webhook_url = webhook_url or Variable.get('SLACK_WEBHOOK_URL', default_var=None)
    
    if not webhook_url:
        logger.warning("Slack не настроен: отсутствует SLACK_WEBHOOK_URL")
        return False
    
    try:
        response = requests.post(webhook_url, json={'text': message}, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Slack уведомление отправлено")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка отправки в Slack: {e}")
        return False

def task_success_alert(context):
    """Уведомление об успешном выполнении задачи"""
    message = f"""
✅ Task Success
DAG: {context['dag'].dag_id}
Task: {context['task'].task_id}
Execution: {context['ds']}
Duration: {context.get('task_duration', 'N/A')}s
    """
    return send_telegram_alert(message)

def task_failure_alert(context):
    """Уведомление об ошибке"""
    message = f"""
❌ Task Failed
DAG: {context['dag'].dag_id}
Task: {context['task'].task_id}
Execution: {context['ds']}
Error: {context.get('exception', 'Unknown error')}
    """
    return send_telegram_alert(message)