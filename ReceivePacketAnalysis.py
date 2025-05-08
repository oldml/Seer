import json # 导入 json 模块，用于处理 JSON 数据
import threading # 导入 threading 模块，用于多线程编程
import logging # 导入 logging 模块，用于日志记录
from typing import Optional, Dict, Any # 从 typing 模块导入类型提示
from dataclasses import dataclass # 从 dataclasses 模块导入 dataclass，用于创建简单的数据类
from Algorithms import Algorithms # 从 Algorithms 文件导入 Algorithms 类

@dataclass # 使用 dataclass 装饰器，自动生成 __init__, __repr__ 等方法
class PacketInfo: # 定义 PacketInfo 数据类，用于存储数据包信息
    """数据包信息"""
    command_id: int # 命令ID
    command_name: str # 命令名称
    packet_data: bytes # 数据包内容

class ReceivePacketAnalysis: # 定义 ReceivePacketAnalysis 类，用于处理接收到的游戏数据包
    """处理接收到的游戏数据包"""

    def __init__(self, algorithms: Algorithms, tcp_socket, userid: int): # 初始化方法
        # 配置日志
        self.logger = logging.getLogger(__name__) # 获取当前模块的 logger 对象

        # 初始化组件
        self.algorithms = algorithms # Algorithms 类的实例，用于加解密
        self.tcp_socket = tcp_socket # TCP socket 连接对象
        self.userid = userid # 用户ID

        # 加载命令配置
        self.command_dict = self._load_command_dict() # 加载命令ID与名称的映射关系

        # 数据包处理相关
        self.current_command_id: Optional[int] = None # 当前等待的特定命令ID
        self.packet_data: Optional[bytes] = None # 存储接收到的特定数据包内容
        self.data_ready_event = threading.Event() # 线程事件，用于通知特定数据包已准备好

        # 接收缓冲区
        self.buffer = bytearray() # 字节数组，用作接收数据的缓冲区
        self.buffer_lock = threading.Lock() # 线程锁，用于保护缓冲区的并发访问

        # 超时设置
        self.receive_timeout = 5.0  # 默认接收超时时间（秒）
        self.running = True # 运行状态标志，控制接收循环

    def _load_command_dict(self) -> Dict[str, Any]: # 加载命令配置文件的私有方法
        """加载命令配置文件

        Returns:
            Dict: 命令字典，键为命令ID字符串，值为包含命令名称等信息的列表或字典
            
        Raises:
            FileNotFoundError: 如果 Command.json 文件不存在
            json.JSONDecodeError: 如果 Command.json 文件格式错误
        """
        try:
            with open('Command.json', 'r') as file: # 打开 Command.json 文件进行读取
                return json.load(file) # 解析 JSON 文件内容并返回字典
        except FileNotFoundError: # 捕获文件未找到异常
            self.logger.error("Command.json 文件不存在") # 记录错误日志
            raise # 重新抛出异常
        except json.JSONDecodeError: # 捕获 JSON 解析异常
            self.logger.error("Command.json 格式错误") # 记录错误日志
            raise # 重新抛出异常

    def receive_data(self): # 接收并处理数据包的主循环方法
        """接收并处理数据包的主循环"""
        while self.running: # 当程序处于运行状态时循环
            try:
                if not self.tcp_socket: # 检查 TCP socket 是否存在
                    self.logger.error('未连接到服务器') # 记录错误日志
                    break # 跳出循环

                # 从 TCP socket 接收数据，最多1024字节
                recv_data = self.tcp_socket.recv(1024)
                if not recv_data: # 如果接收到的数据为空，表示服务器断开连接
                    self.logger.error('服务器断开连接') # 记录错误日志
                    break # 跳出循环

                # 处理接收到的数据包
                with self.buffer_lock: # 获取缓冲区锁，保证线程安全
                    self.buffer.extend(recv_data) # 将接收到的数据追加到缓冲区
                    self._process_buffer() # 调用 _process_buffer 方法处理缓冲区中的数据

            except Exception as e: # 捕获接收数据过程中可能发生的异常
                self.logger.error(f"接收数据时发生错误：{e}") # 记录错误日志
                break # 跳出循环

    def _process_buffer(self): # 处理接收缓冲区中的数据包的私有方法
        """处理接收缓冲区中的数据包"""
        while len(self.buffer) >= 4: # 当缓冲区中的数据长度大于等于4字节（至少包含一个包长度信息）
            try:
                # 从缓冲区前4字节提取数据包长度（大端序）
                packet_length = int.from_bytes(self.buffer[:4], byteorder='big')

                # 检查数据包是否完整，即缓冲区中的数据是否足够一个完整的数据包
                if len(self.buffer) < packet_length:
                    break # 如果数据不完整，则等待更多数据，跳出当前处理循环

                # 提取完整的数据包
                packet_data = bytes(self.buffer[:packet_length])
                # 从缓冲区中移除已提取的数据包
                self.buffer = self.buffer[packet_length:]

                # 解密数据包
                decrypted_data = self.algorithms.decrypt(packet_data)

                # 解析命令ID（从解密后数据的第5到第9字节，大端序）
                command_value = int.from_bytes(decrypted_data[5:9], byteorder='big')
                # 获取命令名称
                command_str = self._get_command_name(command_value)

                # 格式化解密后的数据包为十六进制字符串并记录日志
                formatted_hex = ' '.join(
                    [decrypted_data.hex()[i:i+2] for i in range(0, len(decrypted_data.hex()), 2)]
                ).upper()
                self.logger.info(f"{command_str}: {formatted_hex}") # 记录命令名称和数据包内容

                # 处理特殊命令，例如密钥初始化
                self._handle_special_commands(command_value, decrypted_data)

                # 检查当前接收到的数据包是否是正在等待的特定数据包
                if command_value == self.current_command_id:
                    self._handle_target_packet(decrypted_data) # 如果是，则处理目标数据包

            except Exception as e: # 捕获处理数据包过程中可能发生的异常
                self.logger.error(f"处理数据包时发生错误: {e}") # 记录错误日志
                # 清空缓冲区以防止因错误数据导致的死循环
                self.buffer.clear()
                break # 跳出处理循环

    def _get_command_name(self, command_value: int) -> str: # 根据命令ID获取命令名称的私有方法
        """获取命令名称

        Args:
            command_value: 命令ID (整数)

        Returns:
            str: 命令名称，如果未找到则返回 'Unknown Command'
        """
        # 从 command_dict 中查找命令ID对应的名称，如果找不到，则默认返回 ['Unknown Command']
        return self.command_dict.get(str(command_value), ['Unknown Command'])[0]

    def _handle_special_commands(self, command_value: int, packet_data: bytes): # 处理特殊命令的私有方法
        """处理特殊命令

        Args:
            command_value: 命令ID
            packet_data: 解密后的数据包内容
        """
        if command_value == 1001: # 如果是命令ID为 1001 (通常是登录成功后的密钥交换)
            self.algorithms.InitKey(packet_data, self.userid) # 使用接收到的数据包和用户ID初始化/更新密钥
            self.logger.info('密钥初始化完成') # 记录日志
            # 从数据包的特定位置提取 result 值并更新到 algorithms 对象中
            result = int.from_bytes(packet_data[13:17], byteorder='big')
            self.algorithms.result = result
            self.logger.info(f"Updated result to: {result}") # 记录更新后的 result 值

    def _handle_target_packet(self, packet_data: bytes): # 处理目标数据包的私有方法
        """处理目标数据包

        Args:
            packet_data: 解密后的目标数据包内容
        """
        self.packet_data = packet_data # 将接收到的数据包存储起来
        self.data_ready_event.set() # 设置事件，通知等待方数据已准备好

    def wait_for_specific_data(self, command_id: int, timeout: float = None) -> Optional[bytes]: # 等待特定命令的数据包的方法
        """等待特定命令的数据包

        Args:
            command_id: 要等待的命令ID
            timeout: 超时时间(秒)，如果为 None，则使用默认超时时间

        Returns:
            Optional[bytes]: 接收到的数据包内容，如果超时或发生错误则返回 None
        """
        if timeout is None: # 如果未指定超时时间
            timeout = self.receive_timeout # 使用类定义的默认超时时间

        try:
            self.current_command_id = command_id # 设置当前需要等待的命令ID
            self.data_ready_event.clear() # 清除事件状态，准备等待

            # 等待事件被设置，带有超时时间
            if self.data_ready_event.wait(timeout):
                data = self.packet_data # 获取存储的数据包
                self.packet_data = None # 清空存储的数据包
                self.current_command_id = None # 清空当前等待的命令ID
                return data # 返回获取到的数据
            else:
                self.logger.warning(f"等待命令 {command_id} ({self._get_command_name(command_id)}) 的响应超时") # 记录超时日志
                return None # 超时返回 None

        except Exception as e: # 捕获等待过程中可能发生的异常
            self.logger.error(f"等待数据包时发生错误: {e}") # 记录错误日志
            return None # 发生错误返回 None
        finally: # 无论成功、超时或异常，都执行 finally 块
            self.current_command_id = None # 清空当前等待的命令ID
            self.data_ready_event.clear() # 清除事件状态

    def stop(self): # 停止接收数据的方法
        """停止接收数据"""
        self.running = False # 将运行状态设置为 False，使接收循环退出
        self.data_ready_event.set()  # 设置事件，以解除可能正在等待的线程阻塞

    def clear_buffer(self): # 清空接收缓冲区的方法
        """清空接收缓冲区"""
        with self.buffer_lock: # 获取缓冲区锁
            self.buffer.clear() # 清空缓冲区内容