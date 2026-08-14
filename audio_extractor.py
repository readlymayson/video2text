# -*- coding: utf-8 -*-
"""
Модуль для извлечения аудио из видеофайлов
"""

import os
import logging
from pathlib import Path
from typing import Optional
from moviepy import VideoFileClip
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioExtractor:
    """Класс для извлечения аудио из видеофайлов"""

    # Поддерживаемые форматы видео
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.ogv'
    }

    def __init__(self):
        """Инициализация экстрактора"""
        self.logger = logging.getLogger(__name__)

    def is_supported_format(self, file_path: str) -> bool:
        """
        Проверяет, поддерживается ли формат видеофайла

        Args:
            file_path: Путь к видеофайлу

        Returns:
            bool: True если формат поддерживается
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_VIDEO_FORMATS

    def extract_audio(self, video_path: str, output_path: Optional[str] = None,
                     audio_codec: str = 'pcm_s16le', audio_bitrate: str = '128k') -> str:
        """
        Извлекает аудио из видеофайла и сохраняет в WAV формате

        Args:
            video_path: Путь к видеофайлу
            output_path: Путь для сохранения аудиофайла (опционально)
            audio_codec: Аудио кодек
            audio_bitrate: Битрейт аудио

        Returns:
            str: Путь к извлеченному аудиофайлу

        Raises:
            FileNotFoundError: Если видеофайл не найден
            ValueError: Если формат видео не поддерживается
            Exception: При ошибках обработки
        """
        video_path = Path(video_path)

        # Проверяем существование видеофайла
        if not video_path.exists():
            raise FileNotFoundError(f"Видеофайл не найден: {video_path}")

        # Проверяем поддерживаемый формат
        if not self.is_supported_format(str(video_path)):
            raise ValueError(f"Неподдерживаемый формат видео: {video_path.suffix}")

        # Определяем путь для выходного файла
        if output_path is None:
            output_path = video_path.with_suffix('.wav')
        else:
            output_path = Path(output_path)
            if output_path.suffix.lower() != '.wav':
                output_path = output_path.with_suffix('.wav')

        # Создаем директорию для выходного файла
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Извлечение аудио из {video_path} в {output_path}")

        try:
            # Загружаем видеофайл
            with VideoFileClip(str(video_path)) as video_clip:
                # Получаем аудиодорожку
                audio_clip = video_clip.audio

                if audio_clip is None:
                    raise ValueError(f"В видеофайле {video_path} нет аудиодорожки")

                # Создаем прогресс-бар
                duration = video_clip.duration
                with tqdm(total=100, desc="Извлечение аудио", unit="%") as pbar:
                    def progress_callback(current_time):
                        progress = min(100, (current_time / duration) * 100)
                        pbar.n = progress
                        pbar.refresh()

                    # Извлекаем аудио с прогрессом
                    audio_clip.write_audiofile(
                        str(output_path),
                        codec=audio_codec,
                        bitrate=audio_bitrate
                    )

                    pbar.n = 100
                    pbar.refresh()

            self.logger.info(f"Аудио успешно извлечено: {output_path}")
            return str(output_path)

        except Exception as e:
            error_msg = f"Ошибка при извлечении аудио из {video_path}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_video_info(self, video_path: str) -> dict:
        """
        Получает информацию о видеофайле

        Args:
            video_path: Путь к видеофайлу

        Returns:
            dict: Информация о видео (длительность, размер, наличие аудио и т.д.)
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Видеофайл не найден: {video_path}")

        try:
            with VideoFileClip(str(video_path)) as video_clip:
                info = {
                    'duration': video_clip.duration,
                    'size': video_clip.size,
                    'fps': video_clip.fps,
                    'has_audio': video_clip.audio is not None,
                    'file_size_mb': video_path.stat().st_size / (1024 * 1024)
                }

                if video_clip.audio:
                    info['audio_fps'] = video_clip.audio.fps
                    info['audio_nchannels'] = video_clip.audio.nchannels

                return info

        except Exception as e:
            error_msg = f"Ошибка при получении информации о видео {video_path}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
