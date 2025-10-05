#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Subtitles Downloader
Программа для загрузки субтитров с YouTube видео или целых каналов
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import re
from urllib.parse import urlparse, parse_qs
import requests
import json
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    messagebox.showerror("Ошибка", "Необходимо установить yt-dlp:\npip install yt-dlp")
    exit(1)


class YouTubeSubtitlesDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Subtitles Downloader")
        self.root.geometry("800x600")
        
        # Переменные
        self.download_path = tk.StringVar(value=os.path.expanduser("~/Downloads/Subtitles"))
        self.url_var = tk.StringVar()
        self.language_var = tk.StringVar(value="ru")
        self.auto_translate_var = tk.BooleanVar(value=False)
        self.max_videos_var = tk.StringVar(value="50")
        self.subtitle_format_var = tk.StringVar(value="with_timings")  # with_timings или without_timings
        self.is_downloading = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # URL ввод
        ttk.Label(main_frame, text="URL видео или канала:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Привязываем горячие клавиши для поля URL
        self.url_entry.bind('<Control-v>', self.paste_url)
        self.url_entry.bind('<Control-V>', self.paste_url)
        self.url_entry.bind('<Button-3>', self.show_context_menu)  # Правая кнопка мыши
        
        # Путь сохранения
        ttk.Label(main_frame, text="Папка для сохранения:").grid(row=1, column=0, sticky=tk.W, pady=5)
        path_entry = ttk.Entry(main_frame, textvariable=self.download_path, width=50)
        path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        browse_btn = ttk.Button(main_frame, text="Обзор", command=self.browse_folder)
        browse_btn.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # Настройки языка
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки субтитров", padding="5")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(settings_frame, text="Язык субтитров:").grid(row=0, column=0, sticky=tk.W, pady=2)
        lang_combo = ttk.Combobox(settings_frame, textvariable=self.language_var, width=15)
        lang_combo['values'] = (
            'ru - Русский', 'en - English', 'es - Español', 'fr - Français', 
            'de - Deutsch', 'it - Italiano', 'pt - Português', 'ja - 日本語', 
            'ko - 한국어', 'zh - 中文', 'ar - العربية', 'hi - हिन्दी',
            'tr - Türkçe', 'pl - Polski', 'nl - Nederlands', 'sv - Svenska'
        )
        lang_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Формат субтитров
        ttk.Label(settings_frame, text="Формат субтитров:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        
        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=0, column=3, sticky=tk.W, pady=2, padx=(10, 0))
        
        ttk.Radiobutton(
            format_frame, 
            text="С таймингами", 
            variable=self.subtitle_format_var, 
            value="with_timings"
        ).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            format_frame, 
            text="Без таймингов", 
            variable=self.subtitle_format_var, 
            value="without_timings"
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Обновляем значение по умолчанию
        self.language_var.set('ru - Русский')
        
        # Ограничение количества видео
        ttk.Label(settings_frame, text="Макс. видео с канала:").grid(row=1, column=0, sticky=tk.W, pady=2)
        max_videos_entry = ttk.Entry(settings_frame, textvariable=self.max_videos_var, width=10)
        max_videos_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        info_label = ttk.Label(
            settings_frame, 
            text="Программа автоматически найдет:\n• Оригинальные субтитры\n• Автоматически сгенерированные субтитры\n• Переведенные субтитры",
            font=('TkDefaultFont', 8),
            foreground='gray'
        )
        info_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.download_btn = ttk.Button(
            buttons_frame, 
            text="Скачать субтитры", 
            command=self.start_download
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            buttons_frame, 
            text="Остановить", 
            command=self.stop_download,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(buttons_frame, text="Очистить лог", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог загрузки", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def paste_url(self, event=None):
        """Обработка вставки URL через Ctrl+V"""
        try:
            # Получаем содержимое буфера обмена
            clipboard_content = self.root.clipboard_get()
            
            # Очищаем поле и вставляем новое содержимое
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content.strip())
            
            # Логируем успешную вставку
            if clipboard_content.strip():
                self.log_message(f"URL вставлен из буфера обмена")
                
        except tk.TclError:
            # Буфер обмена пуст или недоступен
            self.log_message("Буфер обмена пуст или недоступен")
        except Exception as e:
            self.log_message(f"Ошибка вставки: {str(e)}")
        
        return "break"  # Предотвращаем стандартную обработку события
    
    def show_context_menu(self, event):
        """Показать контекстное меню для поля URL"""
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # Добавляем пункты меню
        context_menu.add_command(label="Вставить (Ctrl+V)", command=self.paste_url)
        context_menu.add_separator()
        context_menu.add_command(label="Выделить всё", command=lambda: self.url_entry.select_range(0, tk.END))
        context_menu.add_command(label="Очистить", command=lambda: self.url_entry.delete(0, tk.END))
        
        try:
            # Показываем меню в позиции курсора
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def validate_url(self, url):
        """Проверка и определение типа URL"""
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtube\.com/channel/',
            r'youtube\.com/c/',
            r'youtube\.com/@',
            r'youtu\.be/',
            r'youtube\.com/user/'
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def get_video_info(self, url):
        """Получение информации о видео/канале"""
        try:
            max_videos = int(self.max_videos_var.get())
        except ValueError:
            max_videos = 50
            
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Быстрое извлечение только базовой информации
            'playlistend': max_videos,  # Ограничиваем количество видео
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            raise Exception(f"Ошибка получения информации: {str(e)}")
    
    def get_language_code(self):
        """Извлекает код языка из выбранного значения"""
        lang_value = self.language_var.get()
        if ' - ' in lang_value:
            return lang_value.split(' - ')[0]
        return lang_value
    
    def download_subtitles_for_video(self, video_url, video_title, output_dir):
        """Загрузка субтитров для одного видео"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
        lang_code = self.get_language_code()
        
        # Если URL содержит только ID, формируем полный URL
        if not video_url.startswith('http'):
            video_url = f"https://www.youtube.com/watch?v={video_url}"
        
        # Настройки для yt-dlp
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,  # Всегда включаем автоматические субтитры
            'subtitleslangs': [lang_code],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': os.path.join(output_dir, f'{safe_title}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                
            # Поиск файлов субтитров (пробуем разные варианты)
            lang = lang_code
            possible_files = [
                f'{safe_title}.{lang}.vtt',  # Обычные субтитры
                f'{safe_title}.{lang}-{lang}.vtt',  # Автоматически переведенные
                f'{safe_title}.{lang}.auto.vtt',  # Автоматические субтитры
                f'{safe_title}.auto.{lang}.vtt',  # Другой формат автоматических
            ]
            
            # Если язык не английский, пробуем также английские субтитры с переводом
            if lang != 'en':
                possible_files.extend([
                    f'{safe_title}.en-{lang}.vtt',  # Английские переведенные на нужный язык
                    f'{safe_title}.en.auto-{lang}.vtt',  # Автоматические английские переведенные
                ])
            
            # Если ничего не найдено, пробуем английские автоматические
            possible_files.extend([
                f'{safe_title}.en.vtt',
                f'{safe_title}.en.auto.vtt',
                f'{safe_title}.auto.en.vtt',
            ])
            
            found_file = None
            subtitle_type = ""
            
            for vtt_file in possible_files:
                full_path = os.path.join(output_dir, vtt_file)
                if os.path.exists(full_path):
                    found_file = full_path
                    if 'auto' in vtt_file:
                        subtitle_type = " (автоматические)"
                    elif '-' in vtt_file and lang in vtt_file:
                        subtitle_type = " (переведенные)"
                    break
            
            if found_file:
                # Определяем формат файла в зависимости от выбора пользователя
                if self.subtitle_format_var.get() == "with_timings":
                    txt_file = os.path.join(output_dir, f'{safe_title}.{lang}.with_timings.txt')
                else:
                    txt_file = os.path.join(output_dir, f'{safe_title}.{lang}.txt')
                    
                self.convert_vtt_to_txt(found_file, txt_file)
                os.remove(found_file)  # Удаляем VTT файл
                self.log_message(f"✓ Субтитры сохранены{subtitle_type}: {video_title}")
                return True
            else:
                # Попробуем найти любые VTT файлы для этого видео
                import glob
                pattern = os.path.join(output_dir, f'{safe_title}*.vtt')
                vtt_files = glob.glob(pattern)
                
                if vtt_files:
                    # Берем первый найденный файл
                    found_file = vtt_files[0]
                    
                    # Определяем формат файла в зависимости от выбора пользователя
                    if self.subtitle_format_var.get() == "with_timings":
                        txt_file = os.path.join(output_dir, f'{safe_title}.{lang}.with_timings.txt')
                    else:
                        txt_file = os.path.join(output_dir, f'{safe_title}.{lang}.txt')
                        
                    self.convert_vtt_to_txt(found_file, txt_file)
                    os.remove(found_file)
                    self.log_message(f"✓ Субтитры сохранены (найден альтернативный язык): {video_title}")
                    return True
                else:
                    self.log_message(f"✗ Субтитры не найдены для: {video_title}")
                    return False
                
        except Exception as e:
            self.log_message(f"Ошибка загрузки субтитров для '{video_title}': {str(e)}")
            return False
    
    def convert_vtt_to_txt(self, vtt_file, txt_file):
        """Конвертация VTT в простой текстовый формат с таймингами или без"""
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Разбиваем на блоки субтитров
            blocks = re.split(r'\n\s*\n', content)
            text_lines = []
            seen_lines = set()  # Для избежания дублирования
            
            for block in blocks:
                lines = block.strip().split('\n')
                
                # Пропускаем заголовки и пустые блоки
                if not lines or lines[0].startswith('WEBVTT') or lines[0].startswith('NOTE'):
                    continue
                
                time_line = None
                subtitle_lines = []
                
                # Ищем строки с текстом и временные метки
                for line in lines:
                    line = line.strip()
                    
                    # Находим временную метку
                    if '-->' in line:
                        time_line = line
                        continue
                    
                    # Пропускаем номера и пустые строки
                    if re.match(r'^\d+$', line) or not line:
                        continue
                    
                    # Удаляем HTML теги и форматирование
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_line = re.sub(r'&[a-zA-Z]+;', '', clean_line)  # HTML entities
                    clean_line = clean_line.strip()
                    
                    if clean_line and clean_line not in seen_lines:
                        subtitle_lines.append(clean_line)
                        seen_lines.add(clean_line)
                
                # Обрабатываем блок в зависимости от выбранного формата
                if self.subtitle_format_var.get() == "with_timings" and time_line and subtitle_lines:
                    # Извлекаем начальное время
                    start_time = time_line.split('-->')[0].strip()
                    # Убираем миллисекунды для лучшей читаемости
                    start_time = re.sub(r'\.\d+', '', start_time)
                    
                    # Добавляем временную метку и текст
                    text_lines.append(f"[{start_time}] {' '.join(subtitle_lines)}")
                elif subtitle_lines:
                    # Без таймингов - просто добавляем текст
                    text_lines.append(' '.join(subtitle_lines))
            
            # Сохраняем в TXT файл
            with open(txt_file, 'w', encoding='utf-8') as f:
                if self.subtitle_format_var.get() == "with_timings":
                    # С таймингами - каждая строка с временной меткой
                    f.write('\n'.join(text_lines))
                else:
                    # Без таймингов - объединяем в абзацы
                    paragraphs = []
                    current_paragraph = []
                    
                    for line in text_lines:
                        current_paragraph.append(line)
                        
                        # Создаем абзац каждые 2-3 строки или при окончании предложения
                        if (len(current_paragraph) >= 2 and 
                            (line.endswith('.') or line.endswith('!') or line.endswith('?') or len(current_paragraph) >= 3)):
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                    
                    # Добавляем оставшиеся строки
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                    
                    f.write('\n\n'.join(paragraphs))
                
        except Exception as e:
            self.log_message(f"Ошибка конвертации VTT в TXT: {str(e)}")
    
    def download_worker(self):
        """Основной поток загрузки"""
        try:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror("Ошибка", "Введите URL видео или канала")
                return
            
            if not self.validate_url(url):
                messagebox.showerror("Ошибка", "Неверный URL YouTube")
                return
            
            # Создаем папку для сохранения
            output_dir = self.download_path.get()
            os.makedirs(output_dir, exist_ok=True)
            
            self.log_message("Получение информации о видео/канале...")
            info = self.get_video_info(url)
            
            # Логируем выбранный формат
            format_text = "с таймингами" if self.subtitle_format_var.get() == "with_timings" else "без таймингов"
            self.log_message(f"Формат субтитров: {format_text}")
            
            if 'entries' in info:
                # Это плейлист или канал
                videos = info['entries']
                total_videos = len(videos)
                
                # Получаем название канала
                channel_name = info.get('title', info.get('uploader', 'Unknown_Channel'))
                if not channel_name or channel_name == 'Unknown_Channel':
                    # Пробуем получить название из первого видео
                    if videos and videos[0]:
                        channel_name = videos[0].get('uploader', videos[0].get('channel', 'Unknown_Channel'))
                
                # Очищаем название канала от недопустимых символов
                safe_channel_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
                
                # Создаем папку для канала
                channel_output_dir = os.path.join(output_dir, safe_channel_name)
                os.makedirs(channel_output_dir, exist_ok=True)
                
                self.log_message(f"Канал: {channel_name}")
                self.log_message(f"Найдено {total_videos} видео на канале")
                self.log_message(f"Папка для сохранения: {channel_output_dir}")
                
                success_count = 0
                for i, video in enumerate(videos, 1):
                    if not self.is_downloading:
                        self.log_message("Загрузка прервана пользователем")
                        break
                    
                    # Проверяем, что у нас есть необходимая информация о видео
                    if not video:
                        self.log_message(f"[{i}/{total_videos}] Пропуск: нет данных о видео")
                        continue
                        
                    video_title = video.get('title', f'Video_{i}')
                    video_url = video.get('webpage_url', video.get('url', ''))
                    
                    if not video_url:
                        self.log_message(f"[{i}/{total_videos}] Пропуск: нет URL для '{video_title}'")
                        continue
                    
                    self.log_message(f"[{i}/{total_videos}] Загрузка субтитров: {video_title}")
                    
                    try:
                        if self.download_subtitles_for_video(video_url, video_title, channel_output_dir):
                            success_count += 1
                    except Exception as e:
                        self.log_message(f"Ошибка для видео '{video_title}': {str(e)}")
                        continue
                    
                self.log_message(f"Завершено! Успешно загружено субтитров: {success_count}/{total_videos}")
                self.log_message(f"Субтитры сохранены в папке: {channel_output_dir}")
                
            else:
                # Это одно видео
                video_title = info.get('title', 'Unknown_Video')
                channel_name = info.get('uploader', info.get('channel', 'Unknown_Channel'))
                
                # Очищаем название канала от недопустимых символов
                safe_channel_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
                
                # Создаем папку для канала (даже для одного видео)
                channel_output_dir = os.path.join(output_dir, safe_channel_name)
                os.makedirs(channel_output_dir, exist_ok=True)
                
                self.log_message(f"Видео: {video_title}")
                self.log_message(f"Канал: {channel_name}")
                self.log_message(f"Папка для сохранения: {channel_output_dir}")
                
                if self.download_subtitles_for_video(url, video_title, channel_output_dir):
                    self.log_message(f"✓ Субтитры успешно сохранены в папке: {channel_output_dir}")
                else:
                    self.log_message("✗ Не удалось загрузить субтитры")
            
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", str(e))
        
        finally:
            self.is_downloading = False
            self.progress.stop()
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def start_download(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        
        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(target=self.download_worker)
        thread.daemon = True
        thread.start()
    
    def stop_download(self):
        self.is_downloading = False
        self.progress.stop()
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("Загрузка остановлена пользователем")


def main():
    root = tk.Tk()
    app = YouTubeSubtitlesDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
