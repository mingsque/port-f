from .proxy_manager import ProxyManager

#python manage.py runserver --noreload, jango has two process to change code
ProxyManager.instance()
