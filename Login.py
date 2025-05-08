import hashlib, requests, socket, struct # 导入所需模块：hashlib 用于MD5加密，requests 用于HTTP请求，socket 用于网络通信，struct 用于处理字节数据
import logging # 导入 logging 模块

# 配置 logging
logger = logging.getLogger(__name__)
from Algorithms import Algorithms # 从 Algorithms 文件导入 Algorithms 类

class Login(): # 定义 Login 类，处理登录逻辑
    def __init__(self, algorithms: Algorithms): # 初始化方法，接收一个 Algorithms 对象作为参数
        self.algorithms = algorithms # 将传入的 Algorithms 对象赋值给实例变量
        self.serverList = { # 定义服务器列表，键为服务器编号，值为端口号
        1: 1241, 2: 1242, 3: 1243, 4: 1244, 5: 1245, 6: 1246, 7: 1247, 8: 1248, 9: 1249, 10: 1250,
        11: 1251, 12: 1252, 13: 1253, 14: 1254, 15: 1255, 16: 1256, 17: 1257, 18: 1258, 19: 1259, 20: 1260,
        21: 1221, 22: 1222, 23: 1223, 24: 1224, 25: 1225, 26: 1226, 27: 1227, 28: 1228, 29: 1229, 30: 1230,
        31: 1231, 32: 1232, 33: 1233, 34: 1234, 35: 1235, 36: 1236, 37: 1237, 38: 1238, 39: 1239, 40: 1240
        }
        self.tcp_socket = None # 初始化 TCP socket 为 None

    def login(self, userid, password): # 登录方法，接收用户ID和密码
        double_md5_password = self.double_md5(password) # 对密码进行双重MD5加密
        # 获取登录凭证
        recv_data = self.login_verify(userid, double_md5_password) # 调用 login_verify 方法进行登录验证
        recv_body = recv_data[21:37] # 从返回数据中提取凭证部分
        userid_bytes =recv_data[9:13] # 从返回数据中提取用户ID的字节表示
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建 TCP socket
            # 连接到指定服务器和端口（这里固定连接到 serverList[32] 对应的服务器）
            self.tcp_socket.connect(('210.68.8.39', self.serverList[32]))
            # 发送登录请求包
            self.tcp_socket.send(self.LOGIN_IN(userid_bytes, recv_body))
            return self.tcp_socket # 返回建立的 TCP socket 连接
        except KeyboardInterrupt: # 捕获键盘中断异常 (Ctrl+C)
            if self.tcp_socket: # 如果 socket 已创建
                self.tcp_socket.close() # 关闭 socket 连接
            logger.info('断开连接') # 使用 logging 记录断开连接信息

    def get_server_addr(self): # 获取服务器地址的方法
        url = r'http://seer.61.com.tw/config/ip.txt' # 服务器地址配置文件的URL
        r = requests.get(url) # 发送 HTTP GET 请求获取配置文件内容
        server_addr = r.text.split('|')[0].split(':') # 解析配置文件内容，提取IP地址和端口号
        return (server_addr[0], int(server_addr[1])) # 返回服务器地址元组 (IP, port)

    def send_login_packet(self, server_addr, send_data): # 发送登录数据包的方法
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建 TCP socket
        logger.info(f"连接到服务器地址: {server_addr}") # 使用 logging 记录服务器地址
        tcp_socket.connect(server_addr) # 连接到指定的服务器地址
        tcp_socket.send(send_data) # 发送数据包
        recv_data = tcp_socket.recv(1024) # 接收服务器返回的数据，最多1024字节
        tcp_socket.close() # 关闭 socket 连接
        return recv_data # 返回接收到的数据

    @staticmethod # 声明为静态方法，不需要实例化即可调用
    def double_md5(password: str) -> str: # 对密码进行双重MD5加密的方法
        # 计算第一次MD5哈希值
        first_md5 = hashlib.md5(password.encode()).hexdigest() # 将密码编码后计算MD5，并转换为十六进制字符串
        # 计算第二次MD5哈希值
        second_md5 = hashlib.md5(first_md5.encode()).hexdigest() # 对第一次MD5的结果再次进行MD5加密
        return second_md5 # 返回双重MD5加密后的密码

    def login_verify(self, userid, double_md5_password, verification_code_num = b'\x00' * 16, verification_code = b'\x00' * 4): # 登录验证方法
        # 构建基础的登录验证数据包 (packet)
        packet = b'\x00\x00\x00\x931\x00\x00\x00g\t\xc0\xb6\xf7\x00\x00\x00\x00b47906b7958676b2b686a6ec61b1016c\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\xe3^\xbf{\x1dd\xc3\xca\xb6/D/;HI\xd9AAAA\x00\x00unknown\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        # 将用户ID、双重MD5密码、验证码编号和验证码填充到数据包的特定位置
        packet = packet[:9] + struct.pack('>I', userid) + packet[13:17] + double_md5_password.encode() + packet[49:61] + verification_code_num + verification_code + packet[81:]
        # 发送登录验证包并获取返回数据
        recv_data = self.send_login_packet(self.get_server_addr(), packet)
        recv_packet_body = recv_data[17:] # 提取返回数据包的消息体部分
        if recv_packet_body[3] == 0: # 根据消息体特定字节判断登录结果
            logger.info('登录成功') # 使用 logging 记录登录成功信息
        elif recv_packet_body[3] == 1:
            logger.warning('密码错误') # 使用 logging 记录密码错误信息
        elif recv_packet_body[3] == 2:
            logger.warning('验证码错误') # 使用 logging 记录验证码错误信息
            with open(r'验证码.bmp', 'wb')as f: # 将返回的验证码图片数据保存到文件
                f.write(recv_packet_body[24:])
            _verification_code_num = recv_packet_body[4:4+16] # 提取新的验证码编号
            _verification_code = input('请查看保存在代码运行目录下的验证码图片并输入验证码：').encode() # 提示用户输入验证码
            if len(_verification_code) == 4: # 如果输入的验证码长度为4
                # 递归调用 login_verify 方法，使用新的验证码信息进行重试
                self.login_verify(userid, double_md5_password, _verification_code_num, _verification_code)
        return recv_data # 返回服务器的原始响应数据

    def LOGIN_IN(self, userid_bytes, recv_body): # 构建最终登录游戏服务器的数据包
        # 填充 recv_body，使其达到特定长度
        recv_body = recv_body + b'0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        # 使用 algorithms 对象计算结果 (可能是某种序列号或校验和)
        result = self.algorithms.calculate_result(1001, recv_body) # 1001 是命令ID
        # 构建最终的数据包，包含命令头、用户ID字节、计算结果和处理后的 recv_body
        packet_data = b'\x00\x00\x00a1\x00\x00\x03\xe9' + userid_bytes + result.to_bytes(length = 4, byteorder = 'big') + recv_body
        # 使用 algorithms 对象加密数据包
        cipher = self.algorithms.encrypt(packet_data)
        return cipher # 返回加密后的数据包

# if __name__ == '__main__': # 主程序入口，当脚本直接运行时执行
#     algorithms = Algorithms() # 创建 Algorithms 类的实例
#     Login_in = Login(algorithms) # 创建 Login 类的实例，传入 algorithms 对象
#     # 调用 login 方法尝试登录，使用指定的测试用户ID和密码
#     Login_in.login(, '')
