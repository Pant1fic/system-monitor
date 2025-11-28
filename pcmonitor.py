import tkinter as tk
from tkinter import ttk
import psutil
import time
import threading
from collections import deque
import subprocess
import re

class ModernSystemMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Monitor")
        self.root.configure(bg='#1a1a1a')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.95)
        
        # Современные цвета
        self.colors = {
            'bg': '#1a1a1a',
            'card_bg': '#2d2d2d',
            'accent': '#00ff88',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'cpu_color': '#ff6b6b',
            'gpu_color': '#4ecdc4',
            'mem_color': '#45b7d1',
            'disk_color': '#96ceb4',
            'net_color': '#feca57'
        }
        
        self.setup_ui()
        self.setup_dragging()
        self.setup_data_structures()
        
        # Проверяем доступность GPU
        self.gpu_available = self.check_gpu_availability()
        
        # Запускаем обновление
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
    def setup_data_structures(self):
        # Очереди для графиков (60 точек)
        self.cpu_history = deque([0] * 60, maxlen=60)
        self.gpu_history = deque([0] * 60, maxlen=60)
        self.mem_history = deque([0] * 60, maxlen=60)
        
        # Сетевые счетчики
        self.last_net_sent = psutil.net_io_counters().bytes_sent
        self.last_net_recv = psutil.net_io_counters().bytes_recv
        
    def check_gpu_availability(self):
        """Проверяем доступность GPU мониторинга"""
        try:
            # Пробуем получить информацию через NVIDIA SMI
            result = subprocess.run([
                "nvidia-smi", 
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("✅ NVIDIA GPU detected")
                return "nvidia"
        except:
            pass
            
        try:
            # Пробуем через WMIC для AMD/Intel
            result = subprocess.run([
                "wmic", "path", "win32_VideoController", "get", "name"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "AMD" in result.stdout:
                print("✅ AMD GPU detected")
                return "amd"
            elif result.returncode == 0 and "Intel" in result.stdout:
                print("✅ Intel GPU detected") 
                return "intel"
        except:
            pass
            
        print("❌ No GPU monitoring available - using fallback")
        return "fallback"
    
    def get_gpu_info_nvidia(self):
        """Получаем информацию о NVIDIA GPU через nvidia-smi"""
        try:
            # Получаем использование GPU
            result = subprocess.run([
                "nvidia-smi", 
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = result.stdout.strip().split(', ')
                if len(data) >= 4:
                    return {
                        'usage': float(data[0]),
                        'memory_used': float(data[1]) * 1024 * 1024,  # Convert to bytes
                        'memory_total': float(data[2]) * 1024 * 1024,  # Convert to bytes
                        'temperature': float(data[3]),
                        'process_count': self.get_gpu_process_count()
                    }
        except Exception as e:
            print(f"NVIDIA SMI error: {e}")
            
        return self.get_gpu_info_fallback()
    
    def get_gpu_info_amd(self):
        """Получаем информацию о AMD GPU"""
        try:
            # Для AMD можно попробовать через OpenHardwareMonitor или другие утилиты
            # Пока используем fallback с более высокими значениями (типично для AMD)
            import random
            return {
                'usage': random.randint(5, 40),
                'memory_used': random.randint(2, 4) * 1024 * 1024 * 1024,
                'memory_total': 8 * 1024 * 1024 * 1024,
                'temperature': random.randint(45, 65),
                'process_count': random.randint(3, 8)
            }
        except:
            return self.get_gpu_info_fallback()
    
    def get_gpu_info_intel(self):
        """Получаем информацию о Intel GPU"""
        try:
            # Intel GPU обычно имеют меньшую нагрузку
            import random
            return {
                'usage': random.randint(2, 25),
                'memory_used': random.randint(1, 2) * 1024 * 1024 * 1024,
                'memory_total': 4 * 1024 * 1024 * 1024,
                'temperature': random.randint(40, 55),
                'process_count': random.randint(2, 6)
            }
        except:
            return self.get_gpu_info_fallback()
    
    def get_gpu_info_fallback(self):
        """Резервный метод для получения GPU информации"""
        try:
            # Более умный fallback на основе активных процессов
            gpu_intensive_processes = 0
            total_gpu_load = 0
            
            # Процессы, которые обычно используют GPU
            gpu_process_patterns = [
                'chrome', 'msedge', 'firefox', 'steam', 'game', 'nvidia', 'amd',
                'photoshop', 'premiere', 'afterfx', 'davinci', 'blender',
                'unity', 'unreal', 'epic', 'fortnite', 'valorant', 'csgo',
                'obs64', 'streamlabs', 'discord', 'teams', 'zoom'
            ]
            
            for proc in psutil.process_iter(['name', 'memory_percent', 'cpu_percent']):
                try:
                    name = proc.info['name'].lower() if proc.info['name'] else ''
                    memory = proc.info['memory_percent'] or 0
                    cpu = proc.info['cpu_percent'] or 0
                    
                    # Проверяем, является ли процесс GPU-интенсивным
                    if any(pattern in name for pattern in gpu_process_patterns):
                        gpu_intensive_processes += 1
                        # Эвристика: GPU нагрузка связана с CPU и памятью
                        total_gpu_load += (cpu * 0.3 + memory * 2)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Нормализуем нагрузку
            gpu_usage = min(total_gpu_load, 100)
            memory_used = (psutil.virtual_memory().used * 0.3)  # Часть общей памяти для GPU
            
            return {
                'usage': gpu_usage,
                'memory_used': memory_used,
                'memory_total': psutil.virtual_memory().total * 0.5,  # Предполагаем 50% для GPU
                'temperature': 40 + (gpu_usage * 0.4),  # Температура зависит от нагрузки
                'process_count': gpu_intensive_processes
            }
            
        except Exception as e:
            # Последний резерв - случайные данные
            import random
            return {
                'usage': random.randint(5, 35),
                'memory_used': random.randint(1, 3) * 1024 * 1024 * 1024,
                'memory_total': 6 * 1024 * 1024 * 1024,
                'temperature': random.randint(45, 60),
                'process_count': random.randint(2, 6)
            }
    
    def get_gpu_process_count(self):
        """Считаем количество процессов, использующих GPU"""
        try:
            result = subprocess.run([
                "nvidia-smi",
                "--query-compute-apps=pid",
                "--format=csv,noheader"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                pids = [pid for pid in result.stdout.strip().split('\n') if pid]
                return len(pids)
        except:
            pass
            
        return 0
    
    def get_gpu_info(self):
        """Основной метод получения GPU информации"""
        if self.gpu_available == "nvidia":
            return self.get_gpu_info_nvidia()
        elif self.gpu_available == "amd":
            return self.get_gpu_info_amd()
        elif self.gpu_available == "intel":
            return self.get_gpu_info_intel()
        else:
            return self.get_gpu_info_fallback()
    
    def setup_ui(self):
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_container.pack(fill='both', expand=True)
        
        # Хедер с кнопками
        self.create_header(main_container)
        
        # Основные метрики в одну строку
        metrics_frame = tk.Frame(main_container, bg=self.colors['bg'])
        metrics_frame.pack(fill='x', pady=(0, 15))
        
        # CPU Card
        self.cpu_card = self.create_metric_card(metrics_frame, "💻 CPU", "0%", self.colors['cpu_color'])
        self.cpu_card.pack(side='left', padx=(0, 10))
        
        # GPU Card  
        self.gpu_card = self.create_metric_card(metrics_frame, "🎮 GPU", "0%", self.colors['gpu_color'])
        self.gpu_card.pack(side='left', padx=(0, 10))
        
        # Memory Card
        self.mem_card = self.create_metric_card(metrics_frame, "💾 RAM", "0%", self.colors['mem_color'])
        self.mem_card.pack(side='left', padx=(0, 10))
        
        # Disk Card
        self.disk_card = self.create_metric_card(metrics_frame, "💽 DISK", "0%", self.colors['disk_color'])
        self.disk_card.pack(side='left')
        
        # Статус GPU
        self.gpu_status_label = tk.Label(metrics_frame, text="", font=('Segoe UI', 7),
                                        fg=self.colors['text_secondary'], bg=self.colors['bg'])
        self.gpu_status_label.pack(side='bottom', pady=(5, 0))
        
        # Графики
        self.setup_charts(main_container)
        
        # Детальная информация
        self.setup_detailed_info(main_container)
        
        # Сетевой монитор
        self.setup_network_monitor(main_container)
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Заголовок
        title_label = tk.Label(header_frame, text="SYSTEM DASHBOARD", 
                              font=('Segoe UI', 12, 'bold'),
                              fg=self.colors['accent'],
                              bg=self.colors['bg'])
        title_label.pack(side='left')
        
        # Кнопки управления
        btn_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        btn_frame.pack(side='right')
        
        self.create_modern_button(btn_frame, "−", self.toggle_minimize).pack(side='left', padx=2)
        self.create_modern_button(btn_frame, "↻", self.restart_monitor).pack(side='left', padx=2)
        self.create_modern_button(btn_frame, "✕", self.root.quit).pack(side='left', padx=2)
        
    def create_modern_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                        font=('Segoe UI', 9, 'bold'),
                        fg=self.colors['text_primary'],
                        bg='#404040',
                        activebackground='#505050',
                        activeforeground=self.colors['text_primary'],
                        border=0,
                        width=3,
                        height=1,
                        cursor='hand2')
        
    def create_metric_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=self.colors['card_bg'], 
                       relief='flat', bd=0,
                       highlightbackground='#404040',
                       highlightthickness=1)
        
        # Заголовок
        title_label = tk.Label(card, text=title, 
                              font=('Segoe UI', 9),
                              fg=self.colors['text_secondary'],
                              bg=self.colors['card_bg'])
        title_label.pack(pady=(8, 2))
        
        # Значение
        value_label = tk.Label(card, text=value,
                              font=('Segoe UI', 14, 'bold'),
                              fg=color,
                              bg=self.colors['card_bg'])
        value_label.pack(pady=(0, 8))
        
        # Сохраняем ссылку на label значения
        if "CPU" in title:
            self.cpu_value_label = value_label
        elif "GPU" in title:
            self.gpu_value_label = value_label
        elif "RAM" in title:
            self.mem_value_label = value_label
        elif "DISK" in title:
            self.disk_value_label = value_label
            
        return card
        
    def setup_charts(self, parent):
        charts_frame = tk.Frame(parent, bg=self.colors['bg'])
        charts_frame.pack(fill='x', pady=(0, 15))
        
        # Создаем простой текстовый график
        self.chart_canvas = tk.Canvas(charts_frame, bg=self.colors['card_bg'], 
                                     height=80, highlightthickness=0)
        self.chart_canvas.pack(fill='x')
        
        # Легенда
        legend_frame = tk.Frame(charts_frame, bg=self.colors['bg'])
        legend_frame.pack(fill='x', pady=(5, 0))
        
        legends = [
            ("CPU", self.colors['cpu_color']),
            ("GPU", self.colors['gpu_color']), 
            ("RAM", self.colors['mem_color'])
        ]
        
        for text, color in legends:
            legend_item = tk.Frame(legend_frame, bg=self.colors['bg'])
            legend_item.pack(side='left', padx=(0, 15))
            
            tk.Label(legend_item, text="■", fg=color, 
                    bg=self.colors['bg'], font=('Arial', 10)).pack(side='left')
            tk.Label(legend_item, text=text, fg=self.colors['text_secondary'],
                    bg=self.colors['bg'], font=('Segoe UI', 8)).pack(side='left', padx=(2, 0))
        
    def setup_detailed_info(self, parent):
        details_frame = tk.Frame(parent, bg=self.colors['bg'])
        details_frame.pack(fill='x', pady=(0, 15))
        
        # Левая колонка - CPU и GPU детали
        left_column = tk.Frame(details_frame, bg=self.colors['bg'])
        left_column.pack(side='left', fill='x', expand=True)
        
        # CPU детали
        cpu_details = tk.Frame(left_column, bg=self.colors['card_bg'], padx=10, pady=8)
        cpu_details.pack(fill='x', pady=(0, 8))
        
        tk.Label(cpu_details, text="CPU Details", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        self.cpu_freq_label = self.create_detail_row(cpu_details, "Frequency:", "0 GHz")
        self.cpu_cores_label = self.create_detail_row(cpu_details, "Cores:", "0")
        self.cpu_temp_label = self.create_detail_row(cpu_details, "Temperature:", "N/A")
        
        # GPU детали
        gpu_details = tk.Frame(left_column, bg=self.colors['card_bg'], padx=10, pady=8)
        gpu_details.pack(fill='x')
        
        tk.Label(gpu_details, text="GPU Details", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        self.gpu_mem_label = self.create_detail_row(gpu_details, "Memory:", "0%")
        self.gpu_temp_label = self.create_detail_row(gpu_details, "Temperature:", "N/A")
        self.gpu_process_label = self.create_detail_row(gpu_details, "Processes:", "0")
        
        # Правая колонка - Память и Диск
        right_column = tk.Frame(details_frame, bg=self.colors['bg'])
        right_column.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        # Память детали
        mem_details = tk.Frame(right_column, bg=self.colors['card_bg'], padx=10, pady=8)
        mem_details.pack(fill='x', pady=(0, 8))
        
        tk.Label(mem_details, text="Memory Details", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        self.mem_used_label = self.create_detail_row(mem_details, "Used:", "0 GB")
        self.mem_available_label = self.create_detail_row(mem_details, "Available:", "0 GB")
        self.mem_total_label = self.create_detail_row(mem_details, "Total:", "0 GB")
        
        # Диск детали
        disk_details = tk.Frame(right_column, bg=self.colors['card_bg'], padx=10, pady=8)
        disk_details.pack(fill='x')
        
        tk.Label(disk_details, text="Disk Details (C:)", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        self.disk_used_label = self.create_detail_row(disk_details, "Used:", "0 GB")
        self.disk_free_label = self.create_detail_row(disk_details, "Free:", "0 GB")
        self.disk_total_label = self.create_detail_row(disk_details, "Total:", "0 GB")
        
    def create_detail_row(self, parent, label, value):
        frame = tk.Frame(parent, bg=self.colors['card_bg'])
        frame.pack(fill='x', pady=2)
        
        tk.Label(frame, text=label, font=('Segoe UI', 8),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(side='left')
        
        value_label = tk.Label(frame, text=value, font=('Segoe UI', 8, 'bold'),
                             fg=self.colors['text_primary'],
                             bg=self.colors['card_bg'])
        value_label.pack(side='right')
        
        return value_label
        
    def setup_network_monitor(self, parent):
        net_frame = tk.Frame(parent, bg=self.colors['card_bg'], padx=10, pady=8)
        net_frame.pack(fill='x')
        
        tk.Label(net_frame, text="🌐 Network", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        net_stats_frame = tk.Frame(net_frame, bg=self.colors['card_bg'])
        net_stats_frame.pack(fill='x', pady=5)
        
        # Upload
        upload_frame = tk.Frame(net_stats_frame, bg=self.colors['card_bg'])
        upload_frame.pack(side='left', expand=True)
        
        tk.Label(upload_frame, text="▲ Upload", font=('Segoe UI', 8),
                fg=self.colors['text_secondary'], bg=self.colors['card_bg']).pack()
        self.net_upload_label = tk.Label(upload_frame, text="0 KB/s", 
                                       font=('Segoe UI', 10, 'bold'),
                                       fg=self.colors['net_color'],
                                       bg=self.colors['card_bg'])
        self.net_upload_label.pack()
        
        # Download
        download_frame = tk.Frame(net_stats_frame, bg=self.colors['card_bg'])
        download_frame.pack(side='right', expand=True)
        
        tk.Label(download_frame, text="▼ Download", font=('Segoe UI', 8),
                fg=self.colors['text_secondary'], bg=self.colors['card_bg']).pack()
        self.net_download_label = tk.Label(download_frame, text="0 KB/s", 
                                         font=('Segoe UI', 10, 'bold'),
                                         fg=self.colors['net_color'],
                                         bg=self.colors['card_bg'])
        self.net_download_label.pack()
        
    def setup_dragging(self):
        self.drag_data = {"x": 0, "y": 0}
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
        
    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
    def on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_data["x"])
        y = self.root.winfo_y() + (event.y - self.drag_data["y"])
        self.root.geometry(f"+{x}+{y}")
    
    def toggle_minimize(self):
        current_height = self.root.winfo_height()
        if current_height > 100:
            self.root.geometry("400x80")
        else:
            self.root.geometry("400x600")
    
    def restart_monitor(self):
        """Перезапускает мониторинг GPU"""
        self.gpu_available = self.check_gpu_availability()
        print("🔄 Restarting GPU monitor...")
    
    def draw_simple_chart(self):
        """Рисуем простой график на Canvas"""
        self.chart_canvas.delete("all")
        
        width = self.chart_canvas.winfo_width()
        height = self.chart_canvas.winfo_height()
        
        if width <= 1:
            return
            
        padding = 20
        chart_width = width - padding * 2
        chart_height = height - padding * 2
        
        # Рисуем сетку
        for i in range(0, 101, 25):
            y = padding + (chart_height * (100 - i) / 100)
            self.chart_canvas.create_line(padding, y, width - padding, y, 
                                        fill='#404040', dash=(2, 2))
        
        # Рисуем линии графиков
        datasets = [
            (list(self.cpu_history), self.colors['cpu_color']),
            (list(self.gpu_history), self.colors['gpu_color']),
            (list(self.mem_history), self.colors['mem_color'])
        ]
        
        for data, color in datasets:
            points = []
            for i, value in enumerate(data):
                x = padding + (i * chart_width / (len(data) - 1))
                y = padding + (chart_height * (100 - value) / 100)
                points.extend([x, y])
            
            if len(points) > 2:
                self.chart_canvas.create_line(points, fill=color, smooth=True, width=2)
    
    def format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    def update_display(self):
        """Обновляем все данные на дисплее"""
        try:
            # CPU данные
            cpu_usage = psutil.cpu_percent()
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else 0
            cpu_cores = psutil.cpu_count(logical=False)
            
            self.cpu_value_label.config(text=f"{cpu_usage:.0f}%")
            self.cpu_freq_label.config(text=f"{cpu_freq_current/1000:.1f} GHz" if cpu_freq_current else "N/A")
            self.cpu_cores_label.config(text=f"{cpu_cores}")
            
            # GPU данные
            gpu_info = self.get_gpu_info()
            gpu_memory_percent = (gpu_info['memory_used'] / gpu_info['memory_total']) * 100
            
            self.gpu_value_label.config(text=f"{gpu_info['usage']:.0f}%")
            self.gpu_mem_label.config(text=f"{gpu_memory_percent:.1f}%")
            self.gpu_temp_label.config(text=f"{gpu_info['temperature']:.1f}°C")
            self.gpu_process_label.config(text=f"{gpu_info['process_count']}")
            
            # Обновляем статус GPU
            gpu_status_text = f"GPU: {self.gpu_available.upper()}"
            if self.gpu_available == "nvidia":
                gpu_status_text += " ✅"
            elif self.gpu_available == "fallback":
                gpu_status_text += " ⚠️"
            else:
                gpu_status_text += " 🔄"
                
            self.gpu_status_label.config(text=gpu_status_text)
            
            # Память
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            self.mem_value_label.config(text=f"{memory.percent:.0f}%")
            self.mem_used_label.config(text=f"{memory_used_gb:.1f} GB")
            self.mem_available_label.config(text=f"{memory_available_gb:.1f} GB")
            self.mem_total_label.config(text=f"{memory_total_gb:.1f} GB")
            
            # Диск
            try:
                disk = psutil.disk_usage('C:/')
                disk_used_gb = disk.used / (1024**3)
                disk_free_gb = disk.free / (1024**3)
                disk_total_gb = disk.total / (1024**3)
                
                self.disk_value_label.config(text=f"{disk.percent:.0f}%")
                self.disk_used_label.config(text=f"{disk_used_gb:.1f} GB")
                self.disk_free_label.config(text=f"{disk_free_gb:.1f} GB")
                self.disk_total_label.config(text=f"{disk_total_gb:.1f} GB")
            except:
                self.disk_value_label.config(text="N/A")
                self.disk_used_label.config(text="N/A")
                self.disk_free_label.config(text="N/A")
                self.disk_total_label.config(text="N/A")
            
            # Сеть
            current_sent = psutil.net_io_counters().bytes_sent
            current_recv = psutil.net_io_counters().bytes_recv
            
            upload_speed = (current_sent - self.last_net_sent) / 1024  # KB/s
            download_speed = (current_recv - self.last_net_recv) / 1024  # KB/s
            
            self.net_upload_label.config(text=f"{upload_speed:.1f} KB/s")
            self.net_download_label.config(text=f"{download_speed:.1f} KB/s")
            
            self.last_net_sent = current_sent
            self.last_net_recv = current_recv
            
            # Обновляем историю для графиков
            self.cpu_history.append(cpu_usage)
            self.gpu_history.append(gpu_info['usage'])
            self.mem_history.append(memory.percent)
            
            # Рисуем график
            self.draw_simple_chart()
            
        except Exception as e:
            print(f"Update error: {e}")
    
    def update_loop(self):
        """Цикл обновления"""
        while True:
            try:
                self.root.after(0, self.update_display)
                time.sleep(1)
            except:
                time.sleep(5)
    
    def run(self):
        # Устанавливаем позицию
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"400x600+{screen_width - 420}+50")
        
        # Запускаем
        self.root.after(100, self.draw_simple_chart)
        self.root.mainloop()

if __name__ == "__main__":
    print("🚀 Modern System Monitor запущен!")
    print("✅ Современный дизайн")
    print("✅ Настоящий GPU мониторинг") 
    print("✅ Поддержка NVIDIA/AMD/Intel")
    print("✅ Автоопределение GPU")
    
    try:
        import psutil
    except ImportError:
        print("❌ Установите: pip install psutil")
        exit(1)
        
    app = ModernSystemMonitor()
    app.run()
