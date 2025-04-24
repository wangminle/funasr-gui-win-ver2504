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
        self.config_file = os.path.join(self.current_dir, 'config.json')
        self.log_file = os.path.join(self.current_dir, 'funasr_gui_client.log') # 日志文件路径

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
        """查找funasr_wss_client.py脚本路径"""
        # 获取当前工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 优先查找项目根目录下的samples文件夹
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
        samples_dir = os.path.join(project_root, "samples")
        
        if os.path.exists(samples_dir) and os.path.exists(os.path.join(samples_dir, "funasr_wss_client.py")):
            return os.path.join(samples_dir, "funasr_wss_client.py")
        elif os.path.exists(os.path.join(current_dir, "funasr_wss_client.py")):
            return os.path.join(current_dir, "funasr_wss_client.py")
        else:
            return None
            
    def select_file(self):
        """打开文件对话框选择文件"""
        self.status_var.set("正在选择文件...")
        # 注意：此处需要根据 funasr_wss_client.py 支持的格式调整 filetypes
        filetypes = (
            ("音频/视频/脚本文件", "*.wav *.mp3 *.pcm *.mp4 *.mkv *.avi *.flv *.scp"),
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
        """在后台线程中执行 funasr_wss_client.py 脚本"""
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
                logging.warning(f"系统警告: 识别前检测到缺少依赖包: {', '.join(missing_packages)}")
                logging.info("系统事件: 开始自动安装依赖...")
                if not self.install_dependencies(missing_packages):
                    logging.error("系统错误: 依赖安装失败，无法继续执行识别任务")
                    self.status_var.set("错误：依赖安装失败")
                    # Restore button states in finally block
                    return
                logging.info("系统事件: 依赖安装完成，继续执行识别任务")

            # 修改：始终使用本地的 simple_funasr_client.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            local_client_path = os.path.join(current_dir, "simple_funasr_client.py")

            if not os.path.exists(local_client_path):
                logging.error(f"系统错误: 找不到客户端脚本 {local_client_path}")
                self.status_var.set("错误：客户端脚本不存在")
                return

            logging.info(f"系统事件: 使用本地客户端脚本: {local_client_path}")
            script_path = local_client_path # 脚本路径固定为本地客户端

            # 修改：始终将结果目录设置在 src/python-gui-client/results
            result_dir = os.path.join(current_dir, "results")
            os.makedirs(result_dir, exist_ok=True)
            logging.debug(f"调试信息: 创建结果目录: {result_dir}")

            # 构建命令行参数，使用本地脚本和正确的 result_dir
            cmd = [
                sys.executable, # 使用当前 Python 解释器执行脚本
                script_path,    # 使用本地客户端脚本路径
                "--host", ip,
                "--port", port,
                "--mode", "offline", # 固定为 offline 模式
                "--audio_in", audio_in,
                "--use_itn", str(self.use_itn_var.get()),
                "--ssl", str(self.use_ssl_var.get()),
                "--output_dir", result_dir # 使用正确的 result_dir
            ]

            logging.info(f"系统事件: 执行命令: {' '.join(cmd)}")
            logging.debug(f"调试信息: 命令参数详情: {cmd}")

            # 使用 subprocess.Popen 实时获取输出
            env = os.environ.copy()
            # 确保使用UTF-8编码
            env["PYTHONIOENCODING"] = "utf-8"
            logging.debug("调试信息: 设置子进程环境变量 PYTHONIOENCODING=utf-8")
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8', 
                errors='replace', 
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            logging.debug(f"调试信息: 子进程已启动，PID: {process.pid}")

            # 读取 stdout
            logging.info("系统事件: 开始捕获识别脚本输出")
            for line in iter(process.stdout.readline, ''):
                # Remove potential trailing newline before logging
                line = line.strip()
                if line: # Avoid logging empty lines
                    # 这里使用INFO级别记录客户端脚本的输出，将来可以优化为单独类别
                    # 考虑添加"脚本输出:"前缀，使得将来容易分离
                    logging.info(f"脚本输出: {line}")
            process.stdout.close()

            # 读取 stderr
            stderr_output = process.stderr.read().strip()
            if stderr_output:
                logging.error(f"脚本错误: {stderr_output}")

                # Check for common errors and log suggestions
                if "did not receive a valid HTTP response" in stderr_output or "connection closed while reading HTTP status line" in stderr_output:
                    logging.warning("用户提示: 检测到WebSocket握手失败，建议：")
                    logging.warning("用户提示: 1. 检查服务器是否支持WebSocket协议")
                    logging.warning("用户提示: 2. 尝试使用不同的端口（如10096或10097）")
                    logging.warning("用户提示: 3. 查看服务器日志，确认是否正确启动了WebSocket服务")
                    logging.warning("用户提示: 4. 如果使用了SSL，尝试关闭SSL或确保服务器支持SSL")
                elif "cannot call recv while another coroutine is already running recv" in stderr_output:
                    logging.warning("用户提示: 检测到WebSocket协程冲突错误，建议：")
                    logging.warning("用户提示: 1. 请禁用SSL选项后重试")
                    logging.warning("用户提示: 2. 确保没有其他程序正在连接同一个服务器")
                    logging.warning("用户提示: 3. 尝试重启服务器或等待一段时间后再试")

                # Log server configuration suggestions
                logging.warning("用户提示: 服务器配置建议：")
                logging.warning("用户提示: 1. 常见端口: 离线识别(10095)，实时识别(10096)，标点(10097)，翻译(10098)")
                logging.warning("用户提示: 2. 确认服务器启动命令是否包含--port和--ssl参数，并与客户端保持一致")
                logging.warning("用户提示: 3. 尝试直接使用命令行测试: 'telnet 127.0.0.1 10095' 查看端口是否开放")

            process.stderr.close()

            process.wait() # 等待进程结束
            logging.debug(f"调试信息: 子进程已结束，返回代码: {process.returncode}")

            if process.returncode == 0:
                logging.info("系统事件: 识别任务完成")
                self.status_var.set("识别完成")
                
                # 检查并显示识别结果
                result_files = [f for f in os.listdir(result_dir) if f.startswith("text.")]
                if result_files:
                    logging.info(f"系统事件: 识别结果已保存在目录: {result_dir}")
                    newest_file = max([os.path.join(result_dir, f) for f in result_files], key=os.path.getctime)
                    logging.debug(f"调试信息: 找到最新结果文件: {newest_file}")
                    try:
                        with open(newest_file, "r", encoding="utf-8") as f:
                            result_text = f.read().strip()
                            if result_text:
                                # 特殊标记识别结果，未来可以单独显示在"识别结果"选项卡中
                                log_message = f"识别结果 (来自 {os.path.basename(newest_file)}):\n"
                                log_message += "------ RESULT START ------\n"
                                log_message += result_text + "\n"
                                log_message += "------ RESULT END ------"
                                logging.info(log_message)
                            else:
                                logging.warning(f"系统警告: 结果文件 {newest_file} 存在但内容为空")
                    except Exception as e:
                        logging.error(f"系统错误: 读取结果文件 {newest_file} 时出错: {e}", exc_info=True)
                else:
                    logging.warning(f"系统警告: 在目录 {result_dir} 中未找到结果文件 (text.*)。请检查服务器日志获取更多信息。")
            else:
                logging.error(f"系统错误: 识别任务失败，进程返回代码: {process.returncode}")
                self.status_var.set(f"识别失败 (代码: {process.returncode})")
                # Log suggestions
                logging.warning("用户提示: 根据文档，您可能需要尝试：")
                logging.warning("用户提示: 1. 确保服务器已经正确启动")
                logging.warning("用户提示: 2. 如果您使用的是FunASR官方服务器，检查启动命令中是否包含'--certfile 0'选项")
                logging.warning("用户提示: 3. 尝试直接使用官方客户端脚本，例如：")
                logging.warning("用户提示: python funasr_wss_client.py --host 127.0.0.1 --port 10095 --mode offline --audio_in your_audio.wav --output_dir ./results")

        except Exception as e:
            logging.error(f"系统错误: 执行脚本时发生未捕获的错误: {e}", exc_info=True)
            self.status_var.set(f"错误: {e}")
        finally:
            # 无论成功失败，恢复按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.select_button.config(state=tk.NORMAL)
            logging.debug("调试信息: 恢复按钮状态")

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


if __name__ == "__main__":
    # Ensure the script runs from its directory for relative paths to work correctly
    # os.chdir(os.path.dirname(os.path.abspath(__file__))) # Maybe not needed if resources are handled well
    app = FunASRGUIClient()
    app.mainloop() 