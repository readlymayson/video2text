# -*- coding: utf-8 -*-
"""
Приложение для извлечения аудио из видео и его расшифровки с помощью Whisper
"""

import argparse
import sys
import logging
import locale
from pathlib import Path
from typing import Optional

from audio_extractor import AudioExtractor
from transcriber import AudioTranscriber
from video_downloader import VideoDownloader
from utils import (
    validate_video_file, validate_audio_file, create_output_path, setup_logging,
    format_duration, get_file_size_mb, ensure_directory_exists, is_url, validate_url
)

def read_queue_file(queue_path: str) -> list[str]:
    """Читает файл с очередью и возвращает список ссылок/путей"""
    try:
        with open(queue_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл с очередью не найден: {queue_path}")
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла очереди: {str(e)}")

    # Обрабатываем строки: убираем пробелы, игнорируем пустые и комментарии
    queue_items = []
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        queue_items.append(line)

    if not queue_items:
        raise ValueError(f"Файл очереди пуст или содержит только комментарии: {queue_path}")

    return queue_items

def process_single_item(input_path: str, args, logger) -> bool:
    """Обрабатывает один элемент (файл или URL)"""
    try:
        # Определяем тип входных данных
        is_url_input = is_url(input_path)

        if is_url_input:
            logger.info(f"Обработка URL: {input_path}")
            print(f"[URL] Обнаружен URL: {input_path}")
            print("[DOWNLOAD] Начинаем загрузку видео...")

            try:
                # Загружаем видео
                downloader = VideoDownloader()
                video_info = downloader.get_video_info(input_path)
                print(f"[VIDEO] Название: {video_info['title']}")
                print(f"[VIDEO] Автор: {video_info['uploader']}")
                print(f"[VIDEO] Длительность: {format_duration(video_info['duration'])}")
                print(f"[VIDEO] Просмотры: {video_info['view_count']}")

                downloaded_path = downloader.download_video(input_path)
                input_path = downloaded_path
                print(f"[SUCCESS] Видео загружено: {Path(downloaded_path).name}")
                print("-" * 50)

            except Exception as e:
                logger.error(f"Ошибка при загрузке видео: {str(e)}")
                print(f"❌ Ошибка при загрузке видео: {str(e)}", file=sys.stderr)
                return False

        # Проверяем тип файла
        input_path_obj = Path(input_path)
        is_audio, _ = validate_audio_file(str(input_path_obj))
        is_video, _ = validate_video_file(str(input_path_obj))

        # Если файл проходит и как аудио, и как видео (например, .ogg),
        # отдаем приоритет аудио, чтобы избежать лишнего извлечения через moviepy
        if is_audio:
            is_video = False

        if not is_video and not is_audio:
            error_msg = f"Файл не поддерживается или не найден: {input_path}. Поддерживаются видео и аудио форматы."
            logger.error(error_msg)
            print(f"Ошибка: {error_msg}", file=sys.stderr)
            return False

        logger.info(f"Обработка файла: {input_path}")
        logger.info(f"Размер файла: {get_file_size_mb(str(input_path)):.2f} МБ")

        # Создаем выходные пути
        transcript_path = create_output_path(str(input_path), args.output, '.txt')

        # Если это видео, нам нужно извлечь аудио
        if is_video:
            audio_path = create_output_path(str(input_path), args.audio_output, '.wav')
            ensure_directory_exists(audio_path)
        else:
            # Если это уже аудио, используем его напрямую
            audio_path = str(input_path)

        # Флаг для отслеживания, был ли файл загружен из интернета
        is_downloaded_file = is_url_input

        logger.info(f"Выходной файл транскрипции: {transcript_path}")

        # Создаем директории для выходных файлов
        ensure_directory_exists(transcript_path)

        print(f"[START] Начинаем обработку {'видео' if is_video else 'аудио'}...")
        print(f"[FILE] Файл: {input_path_obj.name}")
        print(f"[MODEL] Модель: {args.model}")
        print(f"[LANG] Язык: {args.language}")
        print(f"[OUTPUT] Выход: {Path(transcript_path).name}")
        print("-" * 50)

        # Шаг 1: Получение аудио
        extracted_audio_path = str(audio_path)
        if is_video:
            print("[AUDIO] Шаг 1: Извлечение аудио из видео...")
            extractor = AudioExtractor()

            try:
                extracted_audio_path = extractor.extract_audio(
                    str(input_path),
                    audio_path
                )
                print(f"[SUCCESS] Аудио извлечено: {Path(extracted_audio_path).name}")

                # Получаем информацию о видео
                video_info = extractor.get_video_info(str(input_path))
                duration_str = format_duration(video_info['duration'])
                print(f"[INFO] Длительность: {duration_str}")
                print(f"[INFO] Аудио: {'Да' if video_info['has_audio'] else 'Нет'}")

            except Exception as e:
                logger.error(f"Ошибка при извлечении аудио: {str(e)}")
                print(f"[ERROR] Ошибка при извлечении аудио: {str(e)}", file=sys.stderr)
                return False

            print("-" * 50)
            print("[TRANSCRIBE] Шаг 2: Расшифровка аудио с помощью Whisper...")
        else:
            print("[TRANSCRIBE] Шаг 1: Расшифровка аудио с помощью Whisper...")

        # Шаг 2 (или 1 для аудио): Расшифровка аудио
        try:
            transcriber = AudioTranscriber(model_name=args.model)
            language = None if args.language == 'auto' else args.language

            result = transcriber.transcribe_audio(
                extracted_audio_path,
                language=language,
                output_path=transcript_path
            )

            print(f"[SUCCESS] Транскрипция завершена")

            # Выводим информацию о результате
            detected_lang = result.get('language', 'unknown')
            duration = result.get('duration', 0)
            text_length = len(result.get('text', '').strip())

            print(f"[LANG] Обнаруженный язык: {detected_lang}")
            print(f"[TIME] Длительность: {format_duration(duration)}")
            print(f"[TEXT] Длина текста: {text_length} символов")

        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {str(e)}")
            print(f"[ERROR] Ошибка при транскрибации: {str(e)}", file=sys.stderr)
            return False

        print("-" * 50)

        # Шаг 3: Очистка (только если это было видео и не просили оставить аудио)
        if is_video:
            if not args.keep_audio:
                try:
                    Path(extracted_audio_path).unlink()
                    print(f"[CLEANUP] Временный аудиофайл удален: {Path(extracted_audio_path).name}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный аудиофайл: {str(e)}")
            else:
                print(f"[SAVE] Аудиофайл сохранен: {Path(extracted_audio_path).name}")
            print("-" * 50)

        # Шаг 4: Очистка загруженного файла (если файл был загружен из интернета)
        if is_downloaded_file and not args.keep_video:
            try:
                Path(input_path).unlink()
                print(f"[CLEANUP] Загруженный видеофайл удален: {Path(input_path).name}")
            except Exception as e:
                logger.warning(f"Не удалось удалить загруженный файл: {str(e)}")
        elif is_downloaded_file:
            print(f"[SAVE] Загруженный файл сохранен: {Path(input_path).name}")
        if is_downloaded_file:
            print("-" * 50)

        print("[SUCCESS] Обработка завершена успешно!")
        print(f"[OUTPUT] Транскрипция сохранена в: {transcript_path}")

        # Показываем начало текста если файл небольшой
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                content = f.read()
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"\n[PREVIEW] Предварительный просмотр:\n{preview}")
        except Exception as e:
            logger.warning(f"Не удалось прочитать файл для предварительного просмотра: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке {input_path}: {str(e)}")
        print(f"[ERROR] Неожиданная ошибка: {str(e)}", file=sys.stderr)
        return False

def parse_arguments():
    """Разбирает аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description='Извлечение аудио из видео/аудио и его расшифровка с помощью Whisper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

Одиночные файлы:
  python main.py video.mp4
  python main.py audio.mp3
  python main.py https://vkvideo.ru/video-123456_789012
  python main.py video.mp4 --model base --language ru --output transcript.txt
  python main.py audio.wav --model medium --verbose

Очереди файлов:
  python main.py --queue queue.txt --model base --language ru
  python main.py --queue videos.txt --model medium --keep-audio

Формат файла очереди:
  Каждая строка содержит URL или путь к файлу
  Пустые строки и строки начинающиеся с # игнорируются
  Пример файла queue.txt:
    # Комментарий
    video1.mp4
    https://youtube.com/watch?v=VIDEO_ID
    audio.wav
        """
    )

    parser.add_argument(
        'input_path',
        nargs='?',
        help='Путь к видео/аудиофайлу или URL для загрузки видео'
    )

    parser.add_argument(
        '--queue', '-q',
        help='Путь к файлу с очередью (каждая строка - URL или путь к файлу)'
    )

    parser.add_argument(
        '--model', '-m',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default='base',
        help='Модель Whisper для расшифровки (по умолчанию: base)'
    )

    parser.add_argument(
        '--language', '-l',
        choices=['auto', 'ru', 'en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar', 'hi', 'tr', 'pl', 'uk'],
        default='auto',
        help='Язык аудио (по умолчанию: auto - автоопределение)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Путь к выходному файлу с транскрипцией (по умолчанию: рядом с видео с расширением .txt)'
    )

    parser.add_argument(
        '--keep-audio', '-k',
        action='store_true',
        help='Сохранить извлеченный аудиофайл после обработки'
    )

    parser.add_argument(
        '--keep-video', '-kv',
        action='store_true',
        help='Сохранить загруженное видео после обработки (для URL)'
    )

    parser.add_argument(
        '--audio-output', '-a',
        help='Путь для сохранения извлеченного аудио (по умолчанию: рядом с видео с расширением .wav)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробный вывод информации'
    )

    parser.add_argument(
        '--log-file',
        help='Путь к файлу для записи логов'
    )

    args = parser.parse_args()

    # Проверяем, что указан либо input_path, либо queue
    if not args.input_path and not args.queue:
        parser.error("Необходимо указать либо путь к файлу/URL, либо файл с очередью (--queue)")

    if args.input_path and args.queue:
        parser.error("Нельзя одновременно указывать путь к файлу/URL и файл с очередью (--queue)")

    return args

def main():
    """Главная функция приложения"""
    try:
        # Настраиваем кодировку для корректного отображения кириллицы в Windows
        if sys.platform == 'win32':
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, '')
                except locale.Error:
                    pass

        # Разбираем аргументы
        args = parse_arguments()

        # Настраиваем логирование
        log_level = logging.DEBUG if args.verbose else logging.INFO
        setup_logging(level=log_level, log_file=args.log_file)

        logger = logging.getLogger(__name__)
        logger.info("Запуск приложения video-to-text")

        # Определяем режим работы: одиночный файл или очередь
        if args.queue:
            # Режим очереди
            logger.info(f"Чтение файла очереди: {args.queue}")
            try:
                queue_items = read_queue_file(args.queue)
                print(f"[QUEUE] Найдено {len(queue_items)} элементов в очереди")
                print("-" * 50)

                successful = 0
                failed = 0

                for i, item in enumerate(queue_items, 1):
                    print(f"\n{'='*50}")
                    print(f"[QUEUE] Обработка элемента {i}/{len(queue_items)}: {item}")
                    print(f"{'='*50}")

                    if process_single_item(item, args, logger):
                        successful += 1
                    else:
                        failed += 1

                    print(f"\n[QUEUE] Промежуточные результаты: {successful} успешно, {failed} ошибок")

                print(f"\n{'='*60}")
                print(f"[QUEUE] Обработка очереди завершена!")
                print(f"[QUEUE] Итого: {successful} успешно, {failed} ошибок")
                print(f"{'='*60}")

                if failed > 0:
                    print(f"[WARNING] {failed} элементов обработаны с ошибками")
                    sys.exit(1)

            except Exception as e:
                logger.error(f"Ошибка при обработке очереди: {str(e)}")
                print(f"[ERROR] Ошибка при обработке очереди: {str(e)}", file=sys.stderr)
                sys.exit(1)

        else:
            # Режим одиночного файла
            if process_single_item(args.input_path, args, logger):
                logger.info("Приложение завершено успешно")
            else:
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n[WARNING] Обработка прервана пользователем", file=sys.stderr)
        logger.warning("Обработка прервана пользователем")
        sys.exit(130)

    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        logger.error(error_msg)
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
