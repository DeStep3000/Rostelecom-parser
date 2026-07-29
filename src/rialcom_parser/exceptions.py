class RialcomParserError(Exception):
    """Базовая ошибка приложения."""


class SourceFetchError(RialcomParserError):
    """Не удалось получить страницу с тарифами."""


class SourceStructureError(RialcomParserError):
    """Структура страницы не соответствует ожидаемой."""
