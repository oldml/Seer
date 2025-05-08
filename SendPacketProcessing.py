import logging # 导入 logging 模块，用于日志记录
import time # 导入 time 模块，用于实现延迟
from typing import Optional # 从 typing 模块导入 Optional 类型提示
from Algorithms import Algorithms # 从 Algorithms 文件导入 Algorithms 类

class SendPacketProcessing: # 定义 SendPacketProcessing 类，用于处理游戏数据包的发送
    """处理游戏数据包的发送"""

    def __init__(self, algorithms: Algorithms, tcp_socket, userid: int): # 初始化方法
        # 配置日志
        self.logger = logging.getLogger(__name__) # 获取当前模块的 logger 对象

        # 初始化组件
        self.algorithms = algorithms # Algorithms 类的实例，用于加解密和计算 result
        self.tcp_socket = tcp_socket # TCP socket 连接对象
        self.user_id = userid.to_bytes(length=4, byteorder='big') # 用户ID，转换为4字节大端序字节串

        # 数据包属性 (用于解析和组装过程中的临时存储)
        self.length: Optional[bytes] = None # 数据包总长度 (字节串形式)
        self.version: Optional[int] = None  # 数据包版本号 (整数)
        self.cmd_id: Optional[bytes] = None # 命令ID (字节串形式)
        self.result: Optional[int] = None # 计算结果或序列号 (整数)
        self.body: Optional[bytes] = None # 数据包体 (字节串形式)

        # 重试配置
        self.max_retries = 3 # 最大重试次数
        self.retry_delay = 0.5  # 重试延迟时间（秒）

    def parse_packet(self, packet: bytes) -> 'SendPacketProcessing': # 解析数据包的方法
        """解析数据包

        Args:
            packet: 原始数据包字节串

        Returns:
            self: 返回实例本身以支持链式调用，方便如 self.parse_packet(data).GroupPacket() 的写法

        Raises:
            ValueError: 如果数据包长度小于17字节 (通常是数据包头部固定长度)
        """
        if len(packet) < 17: # 检查数据包长度是否足够包含头部信息
            raise ValueError("数据包长度不足 (至少需要17字节)") # 抛出值错误

        try:
            # 从数据包中提取各个字段
            self.length = packet[0:4] # 包总长度
            self.version = packet[4] # 版本号 (通常是单个字节)
            self.cmd_id = packet[5:9] # 命令ID
            # 注意：user_id 是在 __init__ 中初始化的，这里解析的是 packet 中的 result/序列号字段
            self.result = packet[13:17] # 结果/序列号字段 (通常在 user_id 之后)
            self.body = packet[17:] # 包体内容

            # 记录详细的解析日志 (使用 DEBUG 级别)
            self.logger.debug(
                f"解析数据包:\n"
                f"  Length: {int.from_bytes(self.length, byteorder='big')}\n"
                f"  Version: {self.version}\n"
                f"  CmdId: {int.from_bytes(self.cmd_id, byteorder='big')}\n"
                f"  UserId (from init): {int.from_bytes(self.user_id, byteorder='big')}\n" # 显示初始化时传入的UserId
                f"  Result (from packet): {int.from_bytes(self.result, byteorder='big')}\n" # 显示从包中解析的result
                f"  Body: {self.body.hex().upper()}"
            )

        except Exception as e: # 捕获解析过程中可能发生的其他异常
            self.logger.error(f"解析数据包失败: {e}") # 记录错误日志
            raise # 重新抛出异常

        return self # 返回实例本身，支持链式调用

    def GroupPacket(self, packet: str) -> bytes: # 组装数据包的方法
        """组装数据包

        Args:
            packet: 十六进制字符串格式的原始数据包 (不包含动态计算的 result)

        Returns:
            bytes: 组装并计算了 result 后的完整数据包字节串

        Raises:
            ValueError: 如果输入的十六进制字符串格式错误
        """
        try:
            # 验证并转换十六进制字符串为字节串
            packet_bytes = bytes.fromhex(packet)

            # 解析传入的原始数据包字节串，填充 self.length, self.version, self.cmd_id, self.body 等属性
            self.parse_packet(packet_bytes)

            # 使用 algorithms 对象计算新的 result 值
            # 注意：这里的 self.result 将被 calculate_result 的返回值覆盖
            self.result = self.algorithms.calculate_result(
                int.from_bytes(self.cmd_id, byteorder='big'), # 将命令ID转换为整数传入
                self.body # 传入包体
            )

            # 组装完整的数据包，包含动态计算的 user_id 和 result
            complete_packet = (
                self.length + # 包总长度 (从原始包解析得到)
                self.version.to_bytes(length=1, byteorder='big') + # 版本号
                self.cmd_id + # 命令ID
                self.user_id + # 用户ID (从 __init__ 获取)
                self.result.to_bytes(length=4, byteorder='big') + # 新计算的 result
                self.body # 包体 (从原始包解析得到)
            )

            return complete_packet # 返回组装好的完整数据包

        except ValueError as ve: # 捕获 bytes.fromhex 可能抛出的 ValueError (如包含非十六进制字符)
            self.logger.error(f"封包数据格式错误，请检查十六进制字符串: {packet} - {ve}") # 记录错误日志
            raise # 重新抛出异常
        except Exception as e: # 捕获组装过程中可能发生的其他异常
            self.logger.error(f"组装数据包失败: {e}") # 记录错误日志
            raise # 重新抛出异常

    def SendPacket(self, packed_message: str, retries: int = None) -> bool: # 发送数据包的方法，支持重试
        """发送数据包，支持重试机制

        Args:
            packed_message: 要发送的数据包 (十六进制字符串格式)
            retries: 重试次数，如果为 None，则使用类定义的 self.max_retries

        Returns:
            bool: 发送是否成功 (True 表示成功，False 表示所有尝试均失败)
        """
        if retries is None: # 如果未指定重试次数
            retries = self.max_retries # 使用类定义的默认最大重试次数

        for attempt in range(retries): # 循环尝试发送
            try:
                # 组装数据包 (包含 result 计算)
                packet = self.GroupPacket(packed_message)
                self.logger.info(f'未加密Send封包 (CmdId: {int.from_bytes(self.cmd_id, byteorder="big")}): {packet.hex().upper()}')

                # 加密数据包
                encrypted_packet = self.algorithms.encrypt(packet)
                self.logger.info(f'加密后Send封包 (CmdId: {int.from_bytes(self.cmd_id, byteorder="big")}): {encrypted_packet.hex().upper()}')

                # 通过 TCP socket 发送加密后的数据包
                self.tcp_socket.send(encrypted_packet)
                return True # 发送成功，返回 True

            except Exception as e: # 捕获发送过程中可能发生的异常 (如网络错误、组包错误等)
                self.logger.error(f"发送数据包失败 (尝试 {attempt + 1}/{retries}): {e}") # 记录错误日志
                if attempt < retries - 1: # 如果还未达到最大重试次数
                    time.sleep(self.retry_delay) # 等待一段时间后重试
                # continue 会直接进入下一次循环尝试
        # 如果所有尝试都失败了
        return False # 返回 False 表示发送失败

    def is_connected(self) -> bool: # 检查 socket 连接状态的方法
        """检查socket连接状态"""
        if not self.tcp_socket: # 如果 socket 对象不存在
            return False # 返回未连接
        try:
            # 尝试发送一个空字节或一个简单的心跳字节来探测连接是否仍然有效
            # 注意：对方服务器需要能正确处理这种探测包，或者忽略它
            # 更可靠的方法是检查 socket 的错误状态或使用 socket.getpeername() 等
            self.tcp_socket.send(b'\x00') # 尝试发送一个字节
            return True # 如果发送没有立即引发异常，则认为连接是活动的
        except Exception: # 捕获发送时可能发生的任何异常 (如 BrokenPipeError, ConnectionResetError)
            return False # 发生异常则认为连接已断开

    def reconnect(self) -> bool: # 重新建立连接的方法 (占位)
        """重新建立连接

        Returns:
            bool: 重连是否成功
        """
        # 实际的重连逻辑需要在这里实现
        # 这可能涉及到：
        # 1. 关闭旧的、可能已损坏的 socket
        # 2. 重新创建 socket 对象
        # 3. 调用 Login 类的方法重新执行登录流程以获取新的有效 socket
        # 4. 更新 self.tcp_socket 为新的 socket
        self.logger.warning("reconnect 方法尚未完全实现")
        pass # 目前是空实现
        return False # 假设重连失败，直到实现为止
