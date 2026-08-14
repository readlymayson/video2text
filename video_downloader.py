# -*- coding: utf-8 -*-
"""
Модуль для загрузки видео по URL с помощью yt-dlp
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp

logger = logging.getLogger(__name__)

class VideoDownloader:
    """Класс для загрузки видео по URL"""

    def __init__(self, output_dir: str = "downloads"):
        """
        Инициализация загрузчика видео

        Args:
            output_dir: Директория для сохранения загруженных видео
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def is_valid_url(self, url: str) -> bool:
        """
        Проверяет, является ли строка допустимым URL

        Args:
            url: Строка для проверки

        Returns:
            bool: True если это URL
        """
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None

    def download_video(self, url: str, output_path: Optional[str] = None,
                      format_preference: str = "best") -> str:
        """
        Загружает видео по URL

        Args:
            url: URL видео
            output_path: Путь для сохранения (опционально)
            format_preference: Предпочитаемый формат ('best', 'worst', или специфический формат)

        Returns:
            str: Путь к загруженному файлу

        Raises:
            Exception: При ошибках загрузки
        """
        if not self.is_valid_url(url):
            raise ValueError(f"Недопустимый URL: {url}")

        # Создаем выходной путь если не указан
        if not output_path:
            # Получаем информацию о видео для создания имени файла
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'video')
                    # Очищаем название от недопустимых символов
                    title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    title = title.replace(' ', '_')
                    output_path = str(self.output_dir / f"{title}.%(ext)s")
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о видео: {str(e)}")
                # Используем generic имя
                import time
                timestamp = int(time.time())
                output_path = str(self.output_dir / f"video_{timestamp}.%(ext)s")

        logger.info(f"Начинаем загрузку видео: {url}")
        logger.info(f"Выходной файл: {output_path}")

        # Настройки yt-dlp
        ydl_opts = {
            'outtmpl': output_path,
            'format': format_preference,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Получаем реальный путь к файлу
                actual_path = ydl.prepare_filename(info)
                logger.info(f"Видео успешно загружено: {actual_path}")
                return actual_path

        except Exception as e:
            error_msg = f"Ошибка при загрузке видео: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _progress_hook(self, d: Dict[str, Any]):
        """Хук для отслеживания прогресса загрузки"""
        if d['status'] == 'finished':
            logger.info(f"Загрузка завершена: {d.get('filename', 'unknown')}")
        elif d['status'] == 'downloading':
            # Можно добавить более подробный прогресс если нужно
            pass

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Получает информацию о видео без загрузки

        Args:
            url: URL видео

        Returns:
            Dict: Информация о видео
        """
        if not self.is_valid_url(url):
            raise ValueError(f"Недопустимый URL: {url}")

        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                    'formats': len(info.get('formats', []))
                }
        except Exception as e:
            logger.warning(f"Не удалось получить информацию о видео: {str(e)}")
            return {
                'title': 'Unknown',
                'duration': 0,
                'uploader': 'Unknown',
                'view_count': 0,
                'upload_date': 'Unknown',
                'description': '',
                'formats': 0
            }