import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import random
import importlib
import pip
import asyncio
import time
import json
import ssl
import traceback
import re
# Logging imports
import logging
import logging.handlers
from queue import Queue # For thread-safe GUI updates from logging handler
import queue # Import the queue module to access queue.Empty

# --- Custom GUI Logging Handler ---
class GuiLogHandler(logging.Handler):
    """
    自定义 logging Handler，将日志记录发送到 tkinter Text 控件。
    使用 Queue 实现线程安全。
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.log_queue = Queue()
        self.text_widget.after(100, self.poll_log_queue) # 定期检查队列

    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)

    def poll_log_queue(self):
        # 检查队列中是否有日志记录
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                # 更新 Text 控件
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, record + '\n')
                self.text_widget.see(tk.END) # 滚动到底部
                self.text_widget.configure(state='disabled')
        # 再次调度自己
        self.text_widget.after(100, self.poll_log_queue)

# --- Main Application Class ---
class FunASRGUIClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FunASR GUI Client V2")
        self.geometry("800x600")
        self.connection_status = False  # 连接状态标志

        # 配置文件路径设置
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.current_dir, os.pardir, os.pardir))
        
        # 新的配置和日志文件路径
        self.release_dir = os.path.join(self.project_root, 'release')
        self.config_dir = os.path.join(self.release_dir, 'config')
        self.logs_dir = os.path.join(self.release_dir, 'logs')
        
        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.log_file = os.path.join(self.logs_dir, 'funasr_gui_client.log') # 日志文件路径
        
        # 迁移旧的配置文件和日志文件
        self.migrate_legacy_files()

        # --- Setup Logging ---
        self.setup_logging()

        logging.info("系统事件: 应用程序初始化") # Log application start

        # --- 服务器连接配置区 ---
        server_frame = ttk.LabelFrame(self, text="服务器连接配置")
        server_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(server_frame, text="服务器 IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.ip_entry = ttk.Entry(server_frame, textvariable=self.ip_var, width=30)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(server_frame, text="端口:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar(value="10095") # 默认离线端口
        self.port_entry = ttk.Entry(server_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # Add Connect Server button
        self.connect_button = ttk.Button(server_frame, text="连接服务器", command=self.connect_server)
        self.connect_button.grid(row=0, column=4, padx=15, pady=5, sticky=tk.E)

        # 添加连接状态指示
        self.connection_indicator = ttk.Label(server_frame, text="未连接", foreground="red", font=("Arial", 9, "bold"))
        self.connection_indicator.grid(row=0, column=5, padx=5, pady=5, sticky=tk.E)

        # Make the frame expandable for the button
        server_frame.columnconfigure(4, weight=1)

        # --- 文件选择与执行区 ---
        file_frame = ttk.LabelFrame(self, text="文件选择与执行")
        file_frame.pack(padx=10, pady=5, fill=tk.X)

        self.select_button = ttk.Button(file_frame, text="选择音/视频文件", command=self.select_file)
        self.select_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60, state='readonly')
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # Move Start Recognition button to the right
        self.start_button = ttk.Button(file_frame, text="开始识别", command=self.start_recognition)
        # Place it in the same column as the Connect button, adjusting grid layout
        self.start_button.grid(row=0, column=4, padx=15, pady=5, sticky=tk.E)

        # Make the frame expandable for the button and the entry
        file_frame.columnconfigure(1, weight=1) # Allow file path entry to expand
        file_frame.columnconfigure(4, weight=0) # Keep button size fixed

        # --- 高级选项区 (暂用 Checkbutton 简化) ---
        options_frame = ttk.LabelFrame(self, text="高级选项")
        options_frame.pack(padx=10, pady=5, fill=tk.X)

        self.use_itn_var = tk.IntVar(value=1) # 默认启用 ITN
        self.itn_check = ttk.Checkbutton(options_frame, text="启用 ITN", variable=self.use_itn_var)
        self.itn_check.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)

        self.use_ssl_var = tk.IntVar(value=1) # 修改：默认启用 SSL，因为服务器需要SSL才能连接
        self.ssl_check = ttk.Checkbutton(options_frame, text="启用 SSL", variable=self.use_ssl_var)
        self.ssl_check.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        # Add "Open Log File" button
        self.open_log_button = ttk.Button(options_frame, text="打开日志文件", command=self.open_log_file)
        self.open_log_button.grid(row=0, column=2, padx=15, pady=2, sticky=tk.W) # Position it next to SSL
        
        # Add "Open Results Folder" button
        self.open_results_button = ttk.Button(options_frame, text="打开结果目录", command=self.open_results_folder)
        self.open_results_button.grid(row=0, column=3, padx=15, pady=2, sticky=tk.W) # Position it next to Open Log

        # --- 状态与结果显示区 ---
        # Renamed frame to Log Display Area
        log_frame = ttk.LabelFrame(self, text="运行日志与结果")
        log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Renamed text widget to log_text
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.configure(state='disabled') # 初始设为只读

        # Attach the GUI handler AFTER the text widget is created
        self.attach_gui_log_handler()

        # --- 状态栏 ---
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 加载配置文件（在创建控件后调用，以便可以设置控件值）
        self.load_config()
        
        # 绑定窗口关闭事件，以便在关闭时保存配置
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 检查必要的依赖 (Log the process)
        self.check_dependencies()

    def migrate_legacy_files(self):
        """检查并迁移旧位置的配置文件和日志文件到新位置"""
        # 旧的配置文件路径
        old_config_file = os.path.join(self.current_dir, 'config.json')
        old_log_file = os.path.join(self.current_dir, 'funasr_gui_client.log')
        
        # 如果旧的配置文件存在而新的不存在，则复制
        if os.path.exists(old_config_file) and not os.path.exists(self.config_file):
            try:
                import shutil
                shutil.copy2(old_config_file, self.config_file)
                print(f"已迁移配置文件从 {old_config_file} 到 {self.config_file}")
            except Exception as e:
                print(f"迁移配置文件失败: {e}")
        
        # 如果旧的日志文件存在而新的不存在，则复制
        if os.path.exists(old_log_file) and not os.path.exists(self.log_file):
            try:
                import shutil
                shutil.copy2(old_log_file, self.log_file)
                print(f"已迁移日志文件从 {old_log_file} 到 {self.log_file}")
            except Exception as e:
                print(f"迁移日志文件失败: {e}")

    def setup_logging(self):
        """配置日志记录"""
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_level = logging.INFO # 默认使用INFO级别，可以考虑添加一个选项让用户切换到DEBUG级别

        # Get root logger
        logger = logging.getLogger()
        logger.setLevel(log_level)

        # --- File Handler ---
        # Rotate log file, keep 3 backups, max size 5MB
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

        # 调试时可以启用控制台输出
        # --- Console Handler (optional, for debugging in terminal) ---
        # console_handler = logging.StreamHandler()
        # console_handler.setFormatter(log_formatter)
        # logger.addHandler(console_handler)

        # GUI Handler will be added later in attach_gui_log_handler
        
        # 记录启动事件
        logging.info("系统事件: 应用程序初始化")
        logging.debug(f"调试信息: 日志文件位置: {self.log_file}")
        logging.debug(f"调试信息: 当前工作目录: {os.getcwd()}")
        logging.debug(f"调试信息: Python版本: {sys.version}")

    def attach_gui_log_handler(self):
        """创建并附加 GUI 日志 Handler"""
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_level = logging.getLogger().level # Use the root logger's level

        # --- GUI Handler ---
        self.gui_handler = GuiLogHandler(self.log_text)
        self.gui_handler.setFormatter(log_formatter)
        # self.gui_handler.setLevel(log_level) # Set level for GUI handler too
        # 设置 GUI Handler 的级别为 DEBUG，以便显示所有级别的日志
        self.gui_handler.setLevel(logging.DEBUG)
        logging.debug("调试信息: GUI日志处理器级别设置为 DEBUG")

        # Add GUI Handler to root logger
        logging.getLogger().addHandler(self.gui_handler)
        logging.debug("调试信息: GUI日志处理器已初始化并添加到根记录器")

    def load_config(self):
        """加载上次保存的配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logging.info(f"系统事件: 配置文件已加载: {self.config_file}")
                logging.debug(f"调试信息: 配置内容: {config}")
                # 更新界面控件值
                if 'ip' in config and config['ip']:
                    self.ip_var.set(config['ip'])
                if 'port' in config and config['port']:
                    self.port_var.set(config['port'])
                if 'use_itn' in config:
                    self.use_itn_var.set(config['use_itn'])
                if 'use_ssl' in config:
                    self.use_ssl_var.set(config['use_ssl'])
            else:
                logging.warning("系统警告: 未找到配置文件，使用默认设置")
        except Exception as e:
            logging.error(f"系统错误: 加载配置文件失败: {e}", exc_info=True)
            logging.warning("系统警告: 使用默认配置")
    
    def save_config(self):
        """保存当前配置"""
        try:
            config = {
                'ip': self.ip_var.get(),
                'port': self.port_var.get(),
                'use_itn': self.use_itn_var.get(),
                'use_ssl': self.use_ssl_var.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            self.status_var.set("已保存配置")
            logging.info(f"系统事件: 配置已保存到 {self.config_file}")
            logging.debug(f"调试信息: 保存的配置: {config}")
        except Exception as e:
            self.status_var.set(f"保存配置失败: {e}")
            logging.error(f"系统错误: 保存配置失败: {e}", exc_info=True)
    
    def on_closing(self):
        """窗口关闭时的处理"""
        try:
            logging.info("系统事件: 应用程序关闭")
            self.save_config()
            self.destroy()
        except Exception as e:
            logging.error(f"系统错误: 关闭窗口时出错: {e}", exc_info=True)
            messagebox.showerror("错误", f"关闭窗口时出错: {e}")
            self.destroy()

    def check_dependencies(self):
        """检查必要的依赖是否已安装"""
        logging.info("系统事件: 开始检查必要的依赖")
        required_packages = ['websockets', 'asyncio']
        missing_packages = []
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                logging.debug(f"调试信息: 依赖包 {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                logging.warning(f"系统警告: 依赖包 {package} 未安装")
        
        if missing_packages:
            logging.warning(f"系统警告: 缺少以下依赖包: {', '.join(missing_packages)}")
            logging.info("用户提示: 将在连接服务器时尝试自动安装依赖包")
        else:
            logging.debug("调试信息: 所有必要的依赖都已安装")

    def install_dependencies(self, packages):
        """安装所需的依赖包"""
        for package in packages:
            logging.info(f"系统事件: 开始安装 {package}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logging.info(f"系统事件: {package} 安装成功")
            except subprocess.CalledProcessError as e:
                logging.error(f"系统错误: {package} 安装失败: {e}")
                return False
        return True

    def connect_server(self):
        """实际尝试连接服务器并测试WebSocket可用性"""
        ip = self.ip_var.get()
        port = self.port_var.get()
        ssl_enabled = self.use_ssl_var.get()
        
        # 禁用按钮，防止重复点击
        self.connect_button.config(state=tk.DISABLED)
        
        # 更新连接状态为未连接
        self._update_connection_indicator(False)
        
        self.status_var.set(f"尝试连接 {ip}:{port} (SSL: {'启用' if ssl_enabled else '禁用'})...")
        logging.info(f"用户操作: 尝试连接服务器: {ip}:{port} (SSL: {'启用' if ssl_enabled else '禁用'})")
        logging.debug(f"调试信息: 连接参数 - IP: {ip}, Port: {port}, SSL: {ssl_enabled}")
        
        # 在新线程中执行连接测试
        thread = threading.Thread(target=self._test_connection, args=(ip, port, ssl_enabled), daemon=True)
        thread.start()

    def _test_connection(self, ip, port, ssl_enabled):
        """在后台线程中测试WebSocket连接"""
        try:
            # 检查并安装依赖
            required_packages = ['websockets', 'asyncio']
            missing_packages = []
            
            for package in required_packages:
                try:
                    importlib.import_module(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                logging.warning(f"连接前检测到缺少依赖包: {', '.join(missing_packages)}")
                logging.info("开始自动安装依赖...")
                if not self.install_dependencies(missing_packages):
                    logging.error("依赖安装失败，无法测试连接。")
                    self.status_var.set("错误：依赖安装失败")
                    self.connect_button.config(state=tk.NORMAL)
                    return
                logging.info("依赖安装完成，继续测试连接。")
                
                # 重新导入依赖（修复：移除局部importlib变量）
                for package in required_packages:
                    try:
                        importlib.import_module(package)
                    except ImportError:
                        pass
            
            # 导入websockets模块(必须在安装后导入)
            import websockets
            
            # 运行异步连接测试
            asyncio.run(self._async_test_connection(ip, port, ssl_enabled))
            
        except Exception as e:
            logging.error(f"连接测试时发生错误: {e}", exc_info=True)
            self.status_var.set(f"连接错误: {e}")
            self.connection_status = False
        finally:
            # 恢复按钮状态
            self.connect_button.config(state=tk.NORMAL)

    def _find_script_path(self):
        """查找simple_funasr_client.py脚本路径"""
        # 获取当前工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 优先查找项目根目录下的samples文件夹 (这个逻辑可能不再需要，但保留以防万一)
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
        samples_dir = os.path.join(project_root, "samples")
        
        target_script_name = "simple_funasr_client.py" # 定义目标脚本名称

        # 检查当前目录下是否存在
        if os.path.exists(os.path.join(current_dir, target_script_name)):
            return os.path.join(current_dir, target_script_name)
        # 检查 samples 目录（作为后备）
        elif os.path.exists(samples_dir) and os.path.exists(os.path.join(samples_dir, target_script_name)):
             logging.warning(f"系统警告: 在当前目录未找到 {target_script_name}，但在 {samples_dir} 中找到。建议将脚本放在主程序同目录下。")
             return os.path.join(samples_dir, target_script_name)
        else:
            return None
            
    def select_file(self):
        """打开文件对话框选择文件"""
        self.status_var.set("正在选择文件...")
        # 注意：此处需要根据 funasr_wss_client.py 支持的格式调整 filetypes
        filetypes = (
            ("音频文件", "*.mp3 *.wma *.wav *.ogg *.ac3 *.m4a *.opus *.aac *.pcm"),
            ("视频文件", "*.mp4 *.wmv *.avi *.mov *.mkv *.mpg *.mpeg *.webm *.ts *.flv"),
            ("所有支持的文件", "*.mp3 *.wma *.wav *.ogg *.ac3 *.m4a *.opus *.aac *.pcm *.mp4 *.wmv *.avi *.mov *.mkv *.mpg *.mpeg *.webm *.ts *.flv"),
            ("所有文件", "*.*")
        )
        filepath = filedialog.askopenfilename(title="选择音频/视频文件", filetypes=filetypes)
        if filepath:
            self.file_path_var.set(filepath)
            self.status_var.set(f"已选择文件: {os.path.basename(filepath)}")
            # 记录文件选择事件
            logging.info(f"用户操作: 已选择文件: {filepath}")
            logging.debug(f"调试信息: 文件大小: {os.path.getsize(filepath)} 字节")
            logging.debug(f"调试信息: 文件类型: {os.path.splitext(filepath)[1]}")
            logging.info("用户提示: 准备开始识别...")
        else:
            self.status_var.set("取消选择文件")
            logging.info("用户操作: 取消选择文件")

    def start_recognition(self):
        """启动识别过程"""
        ip = self.ip_var.get()
        port = self.port_var.get()
        audio_in = self.file_path_var.get()

        if not ip or not port:
            logging.error("用户错误: 服务器IP或端口未设置")
            self.status_var.set("错误：缺少服务器信息")
            return
        if not audio_in:
            logging.error("用户错误: 未选择音频/视频文件")
            self.status_var.set("错误：未选择文件")
            return
            
        # 如果未连接服务器，先尝试连接
        if not self.connection_status:
            logging.info("系统事件: 未检测到服务器连接，先尝试连接服务器...")
            # 创建连接测试线程
            thread = threading.Thread(target=self._test_connection, 
                                    args=(ip, port, self.use_ssl_var.get()), 
                                    daemon=True)
            thread.start()
            # 等待连接测试完成
            thread.join(timeout=6)  # 最多等待6秒
            logging.debug(f"调试信息: 连接测试线程完成, 连接状态: {self.connection_status}")
            
            # 检查连接状态
            if not self.connection_status:
                logging.warning("系统警告: 服务器连接测试未成功，但仍将尝试识别")
                logging.warning("用户提示: 如果识别失败，请先使用'连接服务器'按钮测试连接")

        # 禁用按钮，防止重复点击
        self.start_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        self.status_var.set(f"正在识别 {os.path.basename(audio_in)}...")
        logging.info(f"用户操作: 开始识别: {audio_in}")
        logging.info(f"系统事件: 使用服务器: {ip}:{port}")
        logging.debug(f"调试信息: ITN设置: {self.use_itn_var.get()}, SSL设置: {self.use_ssl_var.get()}")

        # 在新线程中运行识别脚本
        thread = threading.Thread(target=self._run_script, args=(ip, port, audio_in), daemon=True)
        thread.start()

    def _run_script(self, ip, port, audio_in):
        """在新线程中运行 simple_funasr_client.py 脚本。"""
        
        # 构造要传递给子进程的参数列表
        # ... (参数构造部分保持不变) ...
        script_path = self._find_script_path()
        if not script_path:
            logging.error("系统错误: 未找到 simple_funasr_client.py 脚本")
            self.status_var.set("错误: 脚本未找到")
            return

        # 设置输出目录到 release/results 文件夹
        results_dir = os.path.join(self.release_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        args = [
            sys.executable,  # 使用当前 Python 解释器
            script_path,
            "--host", ip,
            "--port", str(port),
            "--audio_in", audio_in,
            "--output_dir", results_dir,  # 添加输出目录参数
            # 根据 Checkbutton 状态添加 --no-itn 或 --no-ssl
        ]
        if self.use_itn_var.get() == 0:
            args.append("--no-itn")
        if self.use_ssl_var.get() == 0:
            args.append("--no-ssl")

        # 清空之前的识别结果区域
        self.log_text.configure(state='normal')
        # self.log_text.delete('1.0', tk.END) # 取消启动时清空，不清空之前的系统日志
        self.log_text.configure(state='disabled')
        logging.info(f"任务开始: 正在识别文件 {os.path.basename(audio_in)}")
        logging.info(f"识别结果将保存在: {results_dir}")
        self.status_var.set(f"正在识别: {os.path.basename(audio_in)}...")
        self.start_button.config(state=tk.DISABLED) # 禁用开始按钮

        last_reported_progress = -1 # 用于跟踪上次报告的进度
        last_message_time = time.time() # 初始化上次收到消息的时间
        timeout_duration = 10 # 设置超时时间（秒）

        def run_in_thread():
            nonlocal last_reported_progress, last_message_time # 允许修改外部变量
            process = None
            try:
                logging.debug(f"调试信息: 正在执行命令: {' '.join(args)}")
                # 使用 Popen 启动子进程，捕获 stdout 和 stderr
                process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)

                # 实时读取 stdout
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        stripped_line = line.strip()
                        if stripped_line.startswith("[DEBUG]"):
                            logging.debug(f"客户端调试: {stripped_line}")
                        elif "识别结果" in stripped_line or not stripped_line.startswith("["):
                            logging.info(f"服务器响应: {stripped_line}")
                        else:
                            logging.info(f"客户端事件: {stripped_line}")

                # 等待进程结束并获取返回码和 stderr
                return_code = process.wait()
                stderr_output = process.stderr.read().strip()

                # 检查返回码
                if return_code == 0:
                    logging.info(f"任务成功: 文件 {os.path.basename(audio_in)} 识别完成。")
                    self.after(0, self.status_var.set, "识别完成")
                else:
                    logging.error(f"任务失败: 文件 {os.path.basename(audio_in)} 识别出错。返回码: {return_code}")
                    if stderr_output:
                        logging.error(f"子进程错误输出:\n{stderr_output}")
                    self.after(0, self.status_var.set, f"识别失败 (错误码: {return_code})")
                    # Display error in a popup
                    self.after(0, lambda: messagebox.showerror("识别错误", f"处理文件时发生错误:\n{stderr_output or '未知错误'}"))

            except FileNotFoundError:
                logging.error(f"系统错误: 未找到 Python 解释器或脚本: {sys.executable} 或 {script_path}")
                self.after(0, self.status_var.set, "错误: 无法启动识别脚本")
                self.after(0, lambda: messagebox.showerror("启动错误", "无法找到 Python 解释器或识别脚本。\n请检查 Python 环境和脚本路径。"))
            except Exception as e:
                error_details = traceback.format_exc()
                logging.error(f"系统错误: 运行脚本时出现意外错误: {e}\n{error_details}")
                self.after(0, self.status_var.set, f"意外错误: {e}")
                self.after(0, lambda: messagebox.showerror("意外错误", f"运行识别时发生错误:\n{e}"))
            finally:
                # 确保无论成功或失败，都重新启用按钮
                self.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                self.after(0, lambda: self.select_button.config(state=tk.NORMAL))  # 恢复文件选择按钮
                # 确保进程被终止（如果它仍在运行）
                if process and process.poll() is None:
                    logging.warning("系统警告: 识别过程未正常结束，正在强制终止。")
                    process.terminate()
                    try:
                        process.wait(timeout=5) # Give it a moment to terminate
                    except subprocess.TimeoutExpired:
                        logging.warning("系统警告: 强制终止超时，正在强制杀死进程。")
                        process.kill() # Force kill if terminate doesn't work

        # 启动超时监控
        def check_timeout():
            nonlocal last_message_time
            if time.time() - last_message_time > timeout_duration:
                 if process and process.poll() is None: # 检查进程是否存在且仍在运行
                    logging.warning(f"系统警告: {timeout_duration}秒内未收到服务器响应，可能发生超时。正在尝试终止进程。")
                    process.terminate() # 尝试终止进程
                    try:
                        process.wait(timeout=5) # 等待终止
                    except subprocess.TimeoutExpired:
                        logging.warning("系统警告: 终止进程超时，正在强制杀死。")
                        process.kill() # 强制杀死
                    self.after(0, self.status_var.set, "错误: 连接超时")
                    self.after(0, lambda: messagebox.showerror("连接超时", f"超过 {timeout_duration} 秒未收到服务器响应。"))
                    self.after(0, lambda: self.start_button.config(state=tk.NORMAL)) # 超时后恢复按钮
            elif process and process.poll() is None: # 如果进程仍在运行，继续监控
                self.after(1000, check_timeout) # 每秒检查一次
            # 如果进程已结束，则停止监控
            # elif process and process.poll() is not None:
            #    logging.debug("调试信息：识别进程已结束，停止超时监控。")


        # 在新线程中运行脚本
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True # 设置为守护线程，以便主程序退出时子线程也退出
        thread.start()
        
        # 启动超时检查
        # self.after(1000, check_timeout) # 延迟1秒开始检查

    async def _async_test_connection(self, ip, port, ssl_enabled):
        """异步测试WebSocket连接"""
        import websockets
        
        try:
            # 创建SSL上下文 (直接从funasr_wss_client.py采用相同代码)
            if ssl_enabled == 1:
                # 修复: 使用推荐的SSL上下文创建方法
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                uri = f"wss://{ip}:{port}"
            else:
                uri = f"ws://{ip}:{port}"
                ssl_context = None
            
            logging.info(f"系统事件: 尝试WebSocket连接到: {uri}")
            logging.debug(f"调试信息: SSL上下文: {ssl_context is not None}")
            
            # 设置超时时间
            timeout = 5
            logging.debug(f"调试信息: 连接超时设置: {timeout}秒")
            
            # 使用与funasr_wss_client.py相同的连接参数
            try:
                # 修复：先创建连接对象，然后用await等待连接完成
                connection = websockets.connect(
                    uri, 
                    subprotocols=["binary"], 
                    ping_interval=None, 
                    ssl=ssl_context,
                    proxy=None  # 显式禁用代理
                )
                logging.debug("调试信息: 创建WebSocket连接对象")
                
                # 使用wait_for添加超时，但不作为上下文管理器
                websocket = await asyncio.wait_for(connection, timeout=timeout)
                logging.debug("调试信息: WebSocket连接已建立")
                
                # 使用websocket作为上下文管理器
                async with websocket:
                    # 发送简单的ping消息检查连接
                    try:
                        # 尝试使用与funasr_wss_client.py相同的消息格式
                        message = json.dumps({"mode": "offline", "is_speaking": True})
                        await websocket.send(message)
                        logging.info("系统事件: WebSocket已连接并发送测试消息")
                        logging.debug(f"调试信息: 发送的消息: {message}")
                        
                        # 等待服务器响应，但即使没响应也视为连接成功
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2)
                            logging.info(f"系统事件: 收到WebSocket服务器响应: {response}")
                        except asyncio.TimeoutError:
                            logging.info("系统事件: 未在超时时间内收到WebSocket服务器响应，但连接已建立")
                        
                        logging.info("系统事件: WebSocket连接测试成功")
                        self.status_var.set(f"连接成功: {ip}:{port}")
                        # 更新连接状态为已连接
                        self._update_connection_indicator(True)
                        
                    except websockets.exceptions.ConnectionClosedOK:
                        # 服务器主动关闭连接，也视为连接成功
                        logging.info("系统事件: 服务器主动关闭了WebSocket连接，但连接测试成功")
                        self.status_var.set(f"连接成功: {ip}:{port}")
                        # 更新连接状态为已连接
                        self._update_connection_indicator(True)
                        
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.warning(f"系统警告: WebSocket连接被中断: {e}")
                        logging.warning("系统警告: 服务器可能支持WebSocket但不接受当前消息格式")
                        # 这种情况仍然视为连接部分成功
                        logging.info("用户提示: WebSocket连接基本成功，但服务器可能期望不同的消息格式")
                        self.status_var.set(f"连接部分成功: {ip}:{port}")
                        # 更新连接状态为已连接，但用户应该注意可能有问题
                        self._update_connection_indicator(True)
                    
                    except Exception as e:
                        logging.error(f"系统错误: WebSocket消息发送/接收错误: {e}", exc_info=True)
                        # 连接已建立但通信有问题，仍视为部分成功
                        self.status_var.set(f"连接成功但通信有问题: {ip}:{port}")
                        # 更新连接状态为已连接，但用户应该注意可能有问题
                        self._update_connection_indicator(True)
                    
            except asyncio.TimeoutError:
                logging.error(f"系统错误: 连接 {uri} 超时，服务器无响应")
                self.status_var.set(f"连接超时: {ip}:{port}")
                # 更新连接状态为未连接
                self._update_connection_indicator(False)
            
            except websockets.exceptions.WebSocketException as e:
                logging.error(f"系统错误: WebSocket错误: {e}", exc_info=True)
                
                # 根据不同错误类型提供具体建议
                if isinstance(e, websockets.exceptions.InvalidStatusCode):
                    status_code = getattr(e, "status_code", "未知")
                    logging.error(f"系统错误: 收到HTTP状态码 {status_code}，但不是WebSocket握手")
                    logging.warning("用户提示: 服务器可能不支持WebSocket或在该端口上运行了其他服务")
                
                elif isinstance(e, websockets.exceptions.InvalidMessage):
                    logging.error("系统错误: 收到无效的WebSocket握手消息")
                    # 如果非SSL模式失败，建议尝试SSL模式
                    if ssl_enabled == 0:
                        logging.warning("用户提示: 建议尝试启用SSL选项后重新连接")
                
                self.status_var.set(f"连接失败: WebSocket错误")
                # 更新连接状态为未连接
                self._update_connection_indicator(False)
                
        except ConnectionRefusedError:
            logging.error(f"系统错误: 连接到 {ip}:{port} 被拒绝。服务器可能未启动或端口错误。")
            self.status_var.set(f"连接被拒绝: {ip}:{port}")
            # 更新连接状态为未连接
            self._update_connection_indicator(False)
            
        except Exception as e:
            logging.error(f"系统错误: 测试连接时发生未捕获的异常: {e}", exc_info=True)
            
            # 提供特定错误的建议
            if "ssl" in str(e).lower():
                logging.warning("用户提示: 如果启用了SSL，请尝试禁用SSL选项后重试")
                logging.warning("用户提示: 或者确认服务器是否正确配置了SSL证书")
            elif "connection" in str(e).lower():
                logging.warning("用户提示: 请检查服务器是否正在运行，以及IP和端口是否正确")
                logging.warning("用户提示: 可尝试的端口: 离线识别(10095)，实时识别(10096)，标点(10097)")
            
            self.status_var.set(f"连接错误: {type(e).__name__}")
            # 更新连接状态为未连接
            self._update_connection_indicator(False)
            
    def _update_connection_indicator(self, connected=False):
        """更新连接状态指示器"""
        if connected:
            self.connection_indicator.config(text="已连接", foreground="green")
            self.connection_status = True
            logging.debug("调试信息: 连接状态指示器更新为'已连接'")
        else:
            self.connection_indicator.config(text="未连接", foreground="red")
            self.connection_status = False
            logging.debug("调试信息: 连接状态指示器更新为'未连接'")

    def open_log_file(self):
        """打开日志文件所在的目录或直接打开日志文件"""
        log_file_path = self.log_file
        log_dir = os.path.dirname(log_file_path)
        logging.info(f"用户操作: 尝试打开日志文件: {log_file_path}")
        try:
            if sys.platform == "win32":
                # 在 Windows 上，尝试直接打开文件，如果失败则打开目录
                try:
                    os.startfile(log_file_path)
                    logging.info(f"系统事件: 使用 os.startfile 打开日志文件 {log_file_path}")
                except OSError:
                    logging.warning(f"系统警告: 无法直接打开日志文件 {log_file_path}，尝试打开目录 {log_dir}")
                    os.startfile(log_dir)
                    logging.info(f"系统事件: 使用 os.startfile 打开日志目录 {log_dir}")
            elif sys.platform == "darwin": # macOS
                try:
                    subprocess.run(["open", "-R", log_file_path], check=True) # 在 Finder 中显示文件
                    logging.info(f"系统事件: 使用 'open -R' 在 Finder 中显示日志文件 {log_file_path}")
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logging.error(f"系统错误: 无法在 Finder 中显示日志文件，尝试打开目录: {e}")
                    subprocess.run(["open", log_dir], check=True) # 打开目录
                    logging.info(f"系统事件: 使用 'open' 打开日志目录 {log_dir}")
            else: # Linux and other Unix-like
                try:
                    # 尝试使用 xdg-open 打开目录，更通用
                    subprocess.run(["xdg-open", log_dir], check=True)
                    logging.info(f"系统事件: 使用 'xdg-open' 打开日志目录 {log_dir}")
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logging.error(f"系统错误: 无法使用 xdg-open 打开日志目录 {log_dir}: {e}")
                    messagebox.showwarning("无法打开", f"无法自动打开日志目录。请手动导航至: {log_dir}")
        except Exception as e:
            logging.error(f"系统错误: 打开日志文件/目录时发生错误: {e}", exc_info=True)
            messagebox.showerror("错误", f"无法打开日志文件或目录: {e}")

    def open_results_folder(self):
        """打开结果目录"""
        results_dir = os.path.join(self.release_dir, 'results')
        logging.info(f"用户操作: 尝试打开结果目录: {results_dir}")
        try:
            if sys.platform == "win32":
                # 在 Windows 上，尝试直接打开文件夹，如果失败则打开目录
                try:
                    os.startfile(results_dir)
                    logging.info(f"系统事件: 使用 os.startfile 打开结果目录 {results_dir}")
                except OSError:
                    logging.warning(f"系统警告: 无法直接打开结果目录 {results_dir}，尝试打开目录 {os.path.dirname(results_dir)}")
                    os.startfile(os.path.dirname(results_dir))
                    logging.info(f"系统事件: 使用 os.startfile 打开结果目录父目录 {os.path.dirname(results_dir)}")
            elif sys.platform == "darwin": # macOS
                try:
                    subprocess.run(["open", "-R", results_dir], check=True) # 在 Finder 中显示文件夹
                    logging.info(f"系统事件: 使用 'open -R' 在 Finder 中显示结果目录 {results_dir}")
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logging.error(f"系统错误: 无法在 Finder 中显示结果目录，尝试打开目录: {e}")
                    subprocess.run(["open", os.path.dirname(results_dir)], check=True) # 打开目录
                    logging.info(f"系统事件: 使用 'open' 打开结果目录父目录 {os.path.dirname(results_dir)}")
            else: # Linux and other Unix-like
                try:
                    # 尝试使用 xdg-open 打开目录，更通用
                    subprocess.run(["xdg-open", results_dir], check=True)
                    logging.info(f"系统事件: 使用 'xdg-open' 打开结果目录 {results_dir}")
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logging.error(f"系统错误: 无法使用 xdg-open 打开结果目录 {results_dir}: {e}")
                    messagebox.showwarning("无法打开", f"无法自动打开结果目录。请手动导航至: {results_dir}")
        except Exception as e:
            logging.error(f"系统错误: 打开结果目录时发生错误: {e}", exc_info=True)
            messagebox.showerror("错误", f"无法打开结果目录: {e}")


if __name__ == "__main__":
    # Ensure the script runs from its directory for relative paths to work correctly
    # os.chdir(os.path.dirname(os.path.abspath(__file__))) # Maybe not needed if resources are handled well
    app = FunASRGUIClient()
    app.mainloop() 