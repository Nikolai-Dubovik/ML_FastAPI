import logging

# настройка логов одна на всё приложение и до первого сообщения:
# __init__.py пакета выполняется раньше любого его модуля
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
