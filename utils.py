# -*- coding: utf-8 -*-
"""
Вспомогательные функции для приложения
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

def validate_file_exists(file_path: str) -> bool:
    """
    Проверяет существование файла

    Args:
        file_path: Путь к файлу

    Returns:
        bool: True если файл существует
    """
    return Path(file_path).exists()

def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """
    Проверяет, является ли файл поддерживаемым видеофайлом

    Args:
        file_path: Путь к файлу

    Returns:
        Tuple[bool, str]: (валидность, сообщение об ошибке)
    """
    path = Path(file_path)

    if not path.exists():
        return False, f"Файл не найден: {file_path}"

    supported_extensions = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.ogv'
    }

    if path.suffix.lower() not in supported_extensions:
        return False, f"Неподдерживаемый формат видео: {path.suffix}. Поддерживаемые форматы: {', '.join(supported_extensions)}"

    return True, ""

def validate_audio_file(file_path: str) -> Tuple[bool, str]:
    """
    Проверяет, является ли файл поддерживаемым аудиофайлом

    Args:
        file_path: Путь к файлу

    Returns:
        Tuple[bool, str]: (валидность, сообщение об ошибке)
    """
    path = Path(file_path)

    if not path.exists():
        return False, f"Файл не найден: {file_path}"

    supported_extensions = {'.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a'}

    if path.suffix.lower() not in supported_extensions:
        return False, f"Неподдерживаемый формат аудио: {path.suffix}. Поддерживаемые форматы: {', '.join(supported_extensions)}"

    return True, ""

def create_output_path(input_path: str, output_path: Optional[str] = None,
                      output_extension: str = '.txt') -> str:
    """
    Создает путь для выходного файла

    Args:
        input_path: Путь к входному файлу
        output_path: Желаемый путь к выходному файлу (опционально)
        output_extension: Расширение выходного файла

    Returns:
        str: Путь к выходному файлу
    """
    input_path = Path(input_path)

    if output_path:
        output_path = Path(output_path)
        # Если указан путь без расширения, добавляем его
        if not output_path.suffix:
            output_path = output_path.with_suffix(output_extension)
        # Если указан путь с другим расширением, заменяем его
        elif output_path.suffix.lower() != output_extension.lower():
            output_path = output_path.with_suffix(output_extension)
    else:
        # Создаем выходной файл рядом с входным
        output_path = input_path.with_suffix(output_extension)

    return str(output_path)

def ensure_directory_exists(file_path: str) -> bool:
    """
    Создает директорию для файла если она не существует

    Args:
        file_path: Путь к файлу

    Returns:
        bool: True если директория была создана или уже существовала
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании директории для {file_path}: {str(e)}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """
    Возвращает размер файла в мегабайтах

    Args:
        file_path: Путь к файлу

    Returns:
        float: Размер файла в МБ
    """
    try:
        return Path(file_path).stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0

def format_duration(seconds: float) -> str:
    """
    Форматирует длительность в секундах в читаемый формат

    Args:
        seconds: Длительность в секундах

    Returns:
        str: Отформатированная длительность
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def read_text_file(file_path: str, encoding: str = 'utf-8') -> str:
    """
    Читает текстовый файл с указанной кодировкой

    Args:
        file_path: Путь к файлу
        encoding: Кодировка файла

    Returns:
        str: Содержимое файла

    Raises:
        FileNotFoundError: Если файл не найден
        Exception: При ошибках чтения
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла {file_path}: {str(e)}")

def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Записывает текст в файл с указанной кодировкой

    Args:
        file_path: Путь к файлу
        content: Содержимое для записи
        encoding: Кодировка файла

    Returns:
        bool: True если запись успешна

    Raises:
        Exception: При ошибках записи
    """
    try:
        ensure_directory_exists(file_path)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
        raise Exception(f"Ошибка при записи файла {file_path}: {str(e)}")

def get_supported_video_formats() -> List[str]:
    """Возвращает список поддерживаемых форматов видео"""
    return [
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm',
        'm4v', '3gp', 'mpg', 'mpeg', 'ts', 'mts', 'ogv'
    ]

def get_supported_audio_formats() -> List[str]:
    """Возвращает список поддерживаемых форматов аудио"""
    return ['wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a']

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Настраивает логирование

    Args:
        level: Уровень логирования
        log_file: Путь к файлу логов (опционально)
    """
    # Настройка формата логирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Настройка консольного вывода
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Настройка файла логов если указан
    if log_file:
        ensure_directory_exists(log_file)
        # Используем системную кодировку для логов, чтобы избежать проблем с кириллицей
        import locale
        system_encoding = locale.getpreferredencoding(False)
        file_handler = logging.FileHandler(log_file, encoding=system_encoding)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def clean_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов

    Args:
        filename: Исходное имя файла

    Returns:
        str: Очищенное имя файла
    """
    import re
    # Заменяем недопустимые символы на подчеркивание
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Проверяет, является ли строка допустимым URL

    Args:
        url: Строка для проверки

    Returns:
        Tuple[bool, str]: (валидность, сообщение об ошибке)
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return False, f"Недопустимый URL: {url}"

    return True, ""

def is_url(path_or_url: str) -> bool:
    """
    Определяет, является ли строка URL или путем к файлу

    Args:
        path_or_url: Строка для проверки

    Returns:
        bool: True если это URL
    """
    valid_url, _ = validate_url(path_or_url)
    return valid_url















