import hashlib # 导入 hashlib 模块，用于 MD5 哈希计算
import logging # 导入 logging 模块

# 配置 logging
logger = logging.getLogger(__name__)

class Algorithms: # 定义 Algorithms 类，封装加密、解密等算法
    def __init__(self): # 初始化方法
        self.key = b'!crAckmE4nOthIng:-)'  # 初始化加密密钥
        self.result = 0  # 初始化一个结果变量，可能用于序列号或校验

    def encrypt(self, plain: bytes) -> bytes: # 加密方法，输入明文字节串，输出密文字节串
        cipher_len = len(plain) + 1  # 计算密文长度，比明文长度多1（可能是为了存储额外的校验或结束符）
        plain = plain[4:]  # 跳过明文的前4个字节（通常是封包长度）
        cipher = bytearray(len(plain) + 1)  # 创建一个字节数组用于存放密文，长度为处理后明文长度+1
        # 加密核心逻辑
        j = 0 # 初始化密钥索引
        need_become_zero = False # 标记密钥索引是否需要在下一轮变为0
        for i in range(len(plain)): # 遍历处理后的明文
            if j == 1 and need_become_zero: # 特殊的密钥索引重置逻辑
                j = 0
                need_become_zero = False
            if j == len(self.key): # 如果密钥索引达到密钥长度
                j = 0 # 重置密钥索引
                need_become_zero = True # 标记下一轮j=1时需要重置为0
            cipher[i] = plain[i] ^ self.key[j] # 明文字节与密钥对应字节进行异或操作
            j += 1 # 密钥索引递增
        # 设置密文的最后一个字节为0
        cipher[-1] = 0
        # 对密文进行位操作变换
        for i in range(len(cipher) - 1, 0, -1): # 从后向前遍历密文（不包括第一个字节）
            # 将当前字节左移5位，并与前一个字节右移3位的结果进行或运算
            cipher[i] = ((cipher[i] << 5) & 0xFF) | (cipher[i - 1] >> 3)
        # 对密文的第一个字节进行位操作变换
        cipher[0] = ((cipher[0] << 5) & 0xFF) | 3 # 左移5位并与3进行或运算
        # 计算旋转索引并进行数组旋转
        # 使用明文长度对密钥长度取模，获取密钥中的一个字节，乘以13后对密文长度取模，得到旋转的位数
        result = self.key[len(plain) % len(self.key)] * 13 % len(cipher)
        cipher = cipher[result:len(cipher)] + cipher[0:result] # 将密文数组旋转指定位数
        # 返回拼接原始封包长度（cipher_len）与加密后的数据
        return cipher_len.to_bytes(length = 4, byteorder = 'big') + bytes(cipher)

    def decrypt(self, cipher: bytes) -> bytes: # 解密方法，输入密文字节串，输出明文字节串
        plain_len = len(cipher) - 1  # 计算明文长度，比密文长度少1
        cipher = cipher[4:]  # 跳过密文的前4个字节（通常是封包长度）
        # 计算旋转索引，与加密过程类似，但基于密文长度
        result = self.key[(len(cipher) - 1) % len(self.key)] * 13 % len(cipher)
        # 进行数组反向旋转
        cipher = cipher[len(cipher) - result:len(cipher)] + cipher[0:len(cipher) - result]
        # 初始化明文字节数组
        plain = bytearray(len(cipher) - 1) # 明文长度比处理后的密文长度少1
        # 进行位操作还原，与加密过程的位操作相反
        for i in range(len(cipher) - 1): # 遍历处理后的密文（不包括最后一个字节）
            # 将当前字节右移5位，并与后一个字节左移3位的结果进行或运算
            plain[i] = ((cipher[i] >> 5) & 0xFF) | ((cipher[i + 1] << 3) & 0xFF)
        # 解密核心逻辑，与加密的异或操作相同（异或的特性）
        j = 0 # 初始化密钥索引
        need_become_zero = False # 标记密钥索引是否需要在下一轮变为0
        for i in range(len(plain)): # 遍历明文
            if j == 1 and need_become_zero: # 特殊的密钥索引重置逻辑
                j = 0
                need_become_zero = False
            if j == len(self.key): # 如果密钥索引达到密钥长度
                j = 0 # 重置密钥索引
                need_become_zero = True # 标记下一轮j=1时需要重置为0
            plain[i] = plain[i] ^ self.key[j] # 密文字节与密钥对应字节进行异或操作得到明文字节
            j += 1 # 密钥索引递增
        # 返回拼接原始封包长度（plain_len）与解密后的数据
        return plain_len.to_bytes(length = 4, byteorder = 'big') + bytes(plain)

    def InitKey(self, packet_data: bytes, userid: int): # 初始化或更新密钥的方法
        # 提取通信数据包的最后4个字节
        last_four_bytes = packet_data[-4:]
        # 将这4个字节转换为一个无符号整数（大端序）
        last_uint = int.from_bytes(last_four_bytes, byteorder = 'big')
        # 将得到的整数与用户ID进行异或操作
        xor_result = last_uint ^ userid
        # 将异或结果转换为字符串
        xor_str = str(xor_result)
        # 计算该字符串的MD5哈希值
        md5_hash = hashlib.md5(xor_str.encode()).hexdigest()
        # 取MD5哈希值的前10个字符作为新的通信密钥
        new_key = md5_hash[:10]
        # 更新对象的密钥属性，将其编码为utf-8字节串
        self.key = new_key.encode('utf-8')
        logger.info(f"Updated encryption key to: {self.key!r}") # 使用 logging 记录更新后的密钥

    def MSerial(self, a, b, c, d): # 一个用于计算序列号或某种校验和的函数
        # 执行一系列算术运算
        return a + c + int(a / -3) + (b % 17) + (d % 23) + 120

    def calculate_result(self, cmdId, body): # 计算并更新 result 属性的方法
        crc8_val = 0 # 初始化 CRC8 校验值
        if cmdId > 1000:  # 如果命令ID大于1000
            for byte in body: # 遍历消息体中的每个字节
                crc8_val ^= byte # 计算 CRC8 校验值 (简单异或校验)
        # 调用 MSerial 方法计算新的 result 值
        new_result = self.MSerial(self.result, len(body), crc8_val, cmdId)
        self.result = new_result # 更新对象的 result 属性
        logger.info(f"Updated result to: {new_result}") # 使用 logging 记录更新后的 result 值
        return new_result # 返回新的 result 值
