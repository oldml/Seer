import threading, time, logging # 导入所需模块：threading 用于多线程，time 用于时间相关操作，logging 用于日志记录
import tkinter as tk # 导入 tkinter 模块，用于 GUI (图形用户界面)，但在此代码中似乎未直接使用其组件
from typing import Optional # 从 typing 模块导入 Optional 类型提示，表示一个值可以是某个类型或者 None
from Algorithms import Algorithms # 从 Algorithms 文件导入 Algorithms 类
from Login import Login # 从 Login 文件导入 Login 类
from SendPacketProcessing import SendPacketProcessing # 从 SendPacketProcessing 文件导入 SendPacketProcessing 类
from ReceivePacketAnalysis import ReceivePacketAnalysis # 从 ReceivePacketAnalysis 文件导入 ReceivePacketAnalysis 类
from PetFightPacketManager import PetFightPacketManager # 从 PetFightPacketManager 文件导入 PetFightPacketManager 类
import configparser # 导入 configparser 模块，用于读写配置文件

class Main: # 定义 Main 类，作为程序的主控制类
    def __init__(self): # 初始化方法
        # 配置日志
        self.setup_logging() # 调用 setup_logging 方法配置日志系统

        # 初始化组件
        self.algorithms = Algorithms() # 创建 Algorithms 类的实例
        self.login = Login(self.algorithms) # 创建 Login 类的实例，并传入 algorithms 对象
        self.tcp_socket = None # 初始化 TCP socket 为 None
        self.send_packet_processing = None # 初始化发送数据包处理对象为 None
        self.receive_packet_analysis = None # 初始化接收数据包分析对象为 None
        self.pet_fight_packet_manager = None # 初始化宠物战斗数据包管理器为 None
        self.config = self.load_config() # 加载配置文件

        # 线程控制
        self.running = False # 初始化运行状态为 False
        self.threads = [] # 初始化线程列表为空

    def setup_logging(self): # 配置日志系统的方法
        """配置日志系统"""
        logging.basicConfig( # 基本配置
            level=logging.INFO, # 设置日志级别为 INFO，即只记录 INFO 及以上级别的日志
            format='%(asctime)s - %(levelname)s - %(message)s', # 设置日志格式：时间 - 级别 - 消息
            handlers=[ # 设置日志处理器
                logging.FileHandler('game.log'), # 文件处理器，将日志写入 game.log 文件
                logging.StreamHandler() # 流处理器，将日志输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__) # 获取当前模块的 logger 对象

    def load_config(self) -> configparser.ConfigParser: # 加载配置文件的方法
        """加载配置文件"""
        try:
            config = configparser.ConfigParser() # 创建 ConfigParser 对象
            config.read('config.ini', encoding='utf-8') # 读取 config.ini 文件，使用 utf-8 编码
            return config # 返回配置对象
        except Exception as e: # 捕获加载配置文件时可能发生的异常
            self.logger.error(f"加载配置文件失败: {e}") # 记录错误日志
            raise # 重新抛出异常，使程序终止或由上层处理

    def initialize(self, userid: int, password: str) -> bool: # 初始化连接和组件的方法
        """初始化连接和组件"""
        try:
            self.tcp_socket = self.login.login(userid, password) # 调用 login 对象的 login 方法进行登录，并获取 TCP socket
            if not self.tcp_socket: # 如果登录失败，tcp_socket 为 None
                return False # 返回 False 表示初始化失败

            # 初始化接收数据包分析对象
            self.receive_packet_analysis = ReceivePacketAnalysis(
                self.algorithms, # 传入 algorithms 对象
                self.tcp_socket, # 传入 TCP socket
                userid # 传入用户ID
            )

            # 初始化发送数据包处理对象
            self.send_packet_processing = SendPacketProcessing(
                self.algorithms, # 传入 algorithms 对象
                self.tcp_socket, # 传入 TCP socket
                userid # 传入用户ID
            )

            # 初始化宠物战斗数据包管理器
            self.pet_fight_packet_manager = PetFightPacketManager(
                self.send_packet_processing, # 传入发送数据包处理对象
                self.receive_packet_analysis # 传入接收数据包分析对象
            )

            return True # 返回 True 表示初始化成功

        except Exception as e: # 捕获初始化过程中可能发生的异常
            self.logger.error(f"初始化失败: {e}") # 记录错误日志
            return False # 返回 False 表示初始化失败

    def start_threads(self): # 启动接收和发送线程的方法
        """启动接收和发送线程"""
        self.running = True # 设置运行状态为 True

        # 创建接收数据线程
        receive_thread = threading.Thread(
            target=self.receive_packet_analysis.receive_data, # 线程目标函数为 receive_packet_analysis 对象的 receive_data 方法
            daemon=True # 设置为守护线程，主线程结束时该线程也会结束
        )
        # 创建发送数据（GUI 相关）线程
        send_thread = threading.Thread(
            target=self.send_data_gui, # 线程目标函数为 send_data_gui 方法
            daemon=True # 设置为守护线程
        )

        self.threads = [receive_thread, send_thread] # 将创建的线程添加到线程列表中

        for thread in self.threads: # 遍历线程列表
            thread.start() # 启动线程

    def stop_threads(self): # 停止所有线程的方法
        """停止所有线程"""
        self.running = False # 设置运行状态为 False，通知线程停止
        for thread in self.threads: # 遍历线程列表
            thread.join(timeout=1.0) # 等待线程结束，超时时间为1秒
        self.threads.clear() # 清空线程列表

    def execute_choice(self, choice: int): # 根据选择执行不同操作的方法
        """执行选择的操作"""
        if choice == 0: # 如果选择为 0
            self.execute_daily_routine() # 执行日常任务
        elif choice == 1: # 如果选择为 1
            self.execute_test_routine() # 执行测试任务
        elif choice == 2: # 如果选择为 2
            self.execute_pet_storage_test() # 执行宠物存取测试

    def execute_daily_routine(self): # 执行日常任务的方法
        """执行日常任务

        Returns:
            str: 执行结果描述
        """
        try:
            # 定义日常任务列表，每个元素是一个元组 (任务函数, 任务名称)
            daily_tasks = [
                (self.pet_fight_packet_manager.daily_props_collection, "日常道具收集"),
                (self.pet_fight_packet_manager.battery_dormant_switch, "电池休眠开关"),
                (self.pet_fight_packet_manager.fire_buffer, "火焰增益"),
                (self.pet_fight_packet_manager.experience_training_ground, "经验训练场"),
                (self.pet_fight_packet_manager.learning_training_ground, "学习训练场"),
                (self.pet_fight_packet_manager.trial_of_the_elf_king, "精灵王试炼"),
                (self.pet_fight_packet_manager.x_team_chamber, "X战队密室"),
                (self.pet_fight_packet_manager.titan_mines, "泰坦矿洞"),
            ]

            results = [] # 用于存储每个任务的执行结果
            success = True # 标记所有任务是否都成功
            for task, name in daily_tasks: # 遍历日常任务列表
                try:
                    task() # 执行任务函数
                    self.logger.info(f"{name} 完成") # 记录任务完成日志
                    results.append(f"{name}: 成功") # 添加成功结果
                    time.sleep(0.3) # 等待0.3秒，避免操作过于频繁
                except Exception as e: # 捕获单个任务执行过程中的异常
                    self.logger.error(f"{name} 失败: {e}") # 记录任务失败日志
                    results.append(f"{name}: 失败 ({str(e)})") # 添加失败结果及错误信息
                    success = False # 标记为有任务失败

            return "\n".join(results) # 返回所有任务的执行结果，以换行符分隔

        except Exception as e: # 捕获执行日常任务过程中的其他异常
            self.logger.error(f"执行日常任务失败: {e}") # 记录错误日志
            return f"执行日常任务时发生错误: {str(e)}" # 返回错误信息

    def execute_test_routine(self): # 执行测试任务的方法
        """执行测试任务"""
        try:
            self.pet_fight_packet_manager.battery_dormant_switch() # 执行电池休眠开关操作
            time.sleep(0.3) # 等待
            self.pet_fight_packet_manager.fire_buffer() # 执行火焰增益操作
            time.sleep(0.3) # 等待
            self.pet_fight_packet_manager.titan_vein() # 执行泰坦矿脉相关操作
        except Exception as e: # 捕获测试任务执行过程中的异常
            self.logger.error(f"测试任务执行失败: {e}") # 记录错误日志

    def execute_pet_storage_test(self): # 执行宠物存取测试的方法
        """执行宠物存取测试"""
        try:
            start_time = time.time() # 记录开始时间
            pet_ids_needed = (3512, 3437, 3045) # 需要检查的宠物ID列表
            # 调用宠物战斗数据包管理器的 check_backpack_pets 方法检查背包中的宠物
            self.pet_fight_packet_manager.check_backpack_pets(pet_ids_needed)
            end_time = time.time() # 记录结束时间
            self.logger.info(f"宠物存取测试耗时: {end_time - start_time:.2f}秒") # 记录测试耗时
        except Exception as e: # 捕获宠物存取测试过程中的异常
            self.logger.error(f"宠物存取测试失败: {e}") # 记录错误日志

    def run(self, userid: int, password: str): # 运行主程序的方法
        """运行主程序"""
        try:
            if self.initialize(userid, password): # 调用 initialize 方法进行初始化
                self.start_threads() # 如果初始化成功，则启动线程
                return "登录成功" # 返回登录成功信息
            return "登录失败" # 如果初始化失败，返回登录失败信息
        except Exception as e: # 捕获程序运行过程中的异常
            self.logger.error(f"程序运行失败: {e}") # 记录错误日志
            return f"运行失败: {str(e)}" # 返回运行失败信息

    def cleanup(self): # 清理资源的方法
        """清理资源"""
        self.stop_threads() # 停止所有线程
        if self.tcp_socket: # 如果 TCP socket 存在
            self.tcp_socket.close() # 关闭 TCP socket
            self.tcp_socket = None # 将 TCP socket 设置为 None
            self.logger.info("TCP连接已关闭") # 记录日志

    def send_data_gui(self): # 处理 GUI 相关的数据发送的方法
        """处理 GUI 相关的数据发送

        这个方法在一个单独的线程中运行，负责处理与 GUI 相关的数据发送操作。
        它会在 running 为 False 时停止运行。
        """
        while self.running: # 当程序处于运行状态时循环
            try:
                if not self.tcp_socket: # 如果未连接到服务器
                    self.logger.error('未连接到服务器') # 记录错误日志
                    break # 跳出循环

                # 此处可以添加 GUI 相关的发送逻辑，例如从队列中获取数据并发送
                # 目前这个循环体是空的，只是定期检查连接状态和休眠

                time.sleep(0.1)  # 避免 CPU 占用过高，短暂休眠

            except Exception as e: # 捕获 GUI 数据发送过程中可能发生的异常
                self.logger.error(f"GUI 数据发送失败: {e}") # 记录错误日志
                break # 跳出循环

# if __name__ == '__main__': # 主程序入口，当脚本直接运行时执行
#     main = Main() # 创建 Main 类的实例
#     try:
#         # 调用 run 方法启动程序，使用指定的测试用户ID和密码
#         main.run(, '')
#         # 让主线程保持运行，直到接收到 KeyboardInterrupt (例如 Ctrl+C)
#         # 或者直到所有非守护线程结束。由于这里的 send_data_gui 和 receive_data 是守护线程，
#         # 如果没有其他非守护线程，主线程在 run 方法返回后可能会直接结束。
#         # 为了让程序在登录后能持续运行以接收和处理数据，通常需要一个主循环或等待机制。
#         # 在这个例子中，如果 run() 成功，它会启动守护线程，然后 run() 返回。
#         # 如果没有下面的无限循环或类似的机制，主线程会结束，守护线程也会随之结束。
#         # 这里添加一个简单的循环来保持主线程存活，以便守护线程可以继续工作。
#         while main.running: # 当 main.running 为 True 时，保持主线程运行
#             time.sleep(1) # 每秒检查一次状态

#     except KeyboardInterrupt: # 捕获键盘中断异常 (Ctrl+C)
#         main.logger.info("程序被用户中断") # 记录用户中断日志
#     finally: # 无论是否发生异常，都会执行 finally块中的代码
#         main.logger.info("正在清理资源...") # 记录清理资源日志
#         main.cleanup() # 调用 cleanup 方法清理资源
#         main.logger.info("程序已退出") # 记录程序退出日志
