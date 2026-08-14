# -*- coding: utf-8 -*-
"""
Модуль для расшифровки аудио с помощью Whisper
"""

import os
import logging
import torch
from pathlib import Path
from typing import Optional, List, Dict, Any
import whisper
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Класс для расшифровки аудио с помощью Whisper"""

    # Доступные модели Whisper
    AVAILABLE_MODELS = {
        'tiny': 'tiny',
        'base': 'base',
        'small': 'small',
        'medium': 'medium',
        'large': 'large-v3',
        'large-v2': 'large-v2',
        'large-v1': 'large-v1'
    }

    # Поддерживаемые языки (основные)
    SUPPORTED_LANGUAGES = {
        'auto': None,  # Автоопределение
        'ru': 'ru',    # Русский
        'en': 'en',    # Английский
        'es': 'es',    # Испанский
        'fr': 'fr',    # Французский
        'de': 'de',    # Немецкий
        'it': 'it',    # Итальянский
        'pt': 'pt',    # Португальский
        'zh': 'zh',    # Китайский
        'ja': 'ja',    # Японский
        'ko': 'ko',    # Корейский
        'ar': 'ar',    # Арабский
        'hi': 'hi',    # Хинди
        'tr': 'tr',    # Турецкий
        'pl': 'pl',    # Польский
        'uk': 'uk',    # Украинский
        'cs': 'cs',    # Чешский
        'nl': 'nl',    # Голландский
        'sv': 'sv',    # Шведский
        'da': 'da',    # Датский
        'fi': 'fi',    # Финский
        'no': 'no',    # Норвежский
    }

    def __init__(self, model_name: str = 'base', device: Optional[str] = None):
        """
        Инициализация транскрибатора

        Args:
            model_name: Название модели Whisper
            device: Устройство для вычислений ('cuda', 'cpu' или None для автоопределения)
        """
        self.logger = logging.getLogger(__name__)

        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Неподдерживаемая модель: {model_name}. "
                           f"Доступные модели: {list(self.AVAILABLE_MODELS.keys())}")

        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None

        self.logger.info(f"Инициализация модели {model_name} на устройстве {self.device}")

    def load_model(self):
        """Загружает модель Whisper"""
        if self.model is None:
            try:
                model_size = self.AVAILABLE_MODELS[self.model_name]
                self.logger.info(f"Загрузка модели {model_size}...")

                with tqdm(total=1, desc=f"Загрузка модели {model_size}") as pbar:
                    self.model = whisper.load_model(model_size, device=self.device)
                    pbar.update(1)

                self.logger.info(f"Модель {model_size} успешно загружена")

            except Exception as e:
                error_msg = f"Ошибка при загрузке модели {self.model_name}: {str(e)}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

    def transcribe_audio(self, audio_path: str, language: Optional[str] = None,
                        output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Расшифровывает аудиофайл

        Args:
            audio_path: Путь к аудиофайлу
            language: Язык аудио (None для автоопределения)
            output_path: Путь для сохранения текста (опционально)
            **kwargs: Дополнительные параметры для whisper

        Returns:
            Dict с результатами транскрибации

        Raises:
            FileNotFoundError: Если аудиофайл не найден
            Exception: При ошибках транскрибации
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")

        # Загружаем модель если не загружена
        if self.model is None:
            self.load_model()

        # Проверяем язык
        if language and language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Неподдерживаемый язык: {language}. "
                           f"Доступные языки: {list(self.SUPPORTED_LANGUAGES.keys())}")

        language_code = self.SUPPORTED_LANGUAGES.get(language)

        self.logger.info(f"Начало транскрибации файла {audio_path}")
        if language_code:
            self.logger.info(f"Указанный язык: {language}")
        else:
            self.logger.info("Автоопределение языка")

        try:
            # Выполняем транскрибацию
            with tqdm(total=1, desc="Транскрибация аудио") as pbar:
                result = self.model.transcribe(
                    str(audio_path),
                    language=language_code,
                    verbose=False,
                    **kwargs
                )
                pbar.update(1)

            # Сохраняем результат в файл если указан путь
            if output_path:
                self._save_transcript(result, output_path)

            self.logger.info(f"Транскрибация завершена. Длительность: {result.get('duration', 0):.2f} сек")

            return result

        except Exception as e:
            error_msg = f"Ошибка при транскрибации {audio_path}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _save_transcript(self, result: Dict[str, Any], output_path: str):
        """
        Сохраняет результат транскрибации в файл

        Args:
            result: Результат транскрибации от Whisper
            output_path: Путь для сохранения
        """
        output_path = Path(output_path)

        # Создаем директорию если не существует
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Записываем основную информацию
                duration = result.get('duration', 0)
                detected_language = result.get('language', 'unknown')

                f.write(f"Транскрибация аудио\n")
                f.write(f"Длительность: {duration:.2f} секунд\n")
                f.write(f"Обнаруженный язык: {detected_language}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"{'='*50}\n\n")

                # Записываем текст
                text = result.get('text', '').strip()
                f.write(text)

                # Записываем сегменты с timestamps если доступны
                segments = result.get('segments', [])
                if segments:
                    f.write(f"\n\n{'='*50}\n")
                    f.write("Сегменты с временными метками:\n\n")

                    for segment in segments:
                        start = segment.get('start', 0)
                        end = segment.get('end', 0)
                        segment_text = segment.get('text', '').strip()

                        if segment_text:
                            f.write(f"[{start:.2f}s - {end:.2f}s]: {segment_text}\n")

            self.logger.info(f"Транскрипция сохранена в: {output_path}")

        except Exception as e:
            error_msg = f"Ошибка при сохранении транскрипции в {output_path}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о загруженной модели

        Returns:
            Dict с информацией о модели
        """
        if self.model is None:
            return {
                'model_name': self.model_name,
                'loaded': False,
                'device': self.device
            }

        return {
            'model_name': self.model_name,
            'loaded': True,
            'device': self.device,
            'model_size': self.AVAILABLE_MODELS[self.model_name],
            'torch_device': str(self.model.device)
        }

    @classmethod
    def list_available_models(cls) -> List[str]:
        """Возвращает список доступных моделей"""
        return list(cls.AVAILABLE_MODELS.keys())

    @classmethod
    def list_supported_languages(cls) -> List[str]:
        """Возвращает список поддерживаемых языков"""
        return list(cls.SUPPORTED_LANGUAGES.keys())















