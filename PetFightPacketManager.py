import time
import logging
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from SendPacketProcessing import SendPacketProcessing
from ReceivePacketAnalysis import ReceivePacketAnalysis

@dataclass
class PetInfo:
    """宠物信息"""
    pet_id: int
    timestamp: int
    location: str  # "backpack" 或 "warehouse"

class PetFightError(Exception):
    """宠物战斗相关错误"""
    pass

class PetFightPacketManager:
    """管理宠物战斗相关的数据包"""

    def __init__(self, send_packet_processing: SendPacketProcessing, 
                 receive_packet_analysis: ReceivePacketAnalysis):
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.send_packet_processing = send_packet_processing
        self.receive_packet_analysis = receive_packet_analysis
        
        # 战斗配置
        self.battle_timeout = 3.0  # 秒
        self.operation_delay = 0.3  # 秒
        
        # 缓存
        self.pet_cache: Dict[int, PetInfo] = {}
        
        # 战斗状态
        self.is_fighting = False
        self.current_battle_type: Optional[str] = None

    def check_backpack_pets(self, pet_ids: Tuple[int, ...]) -> bool:
        """检查背包里是否有指定的宠物
        
        Args:
            pet_ids: 要检查的宠物ID元组
            
        Returns:
            bool: 是否成功完成检查和处理
            
        Raises:
            PetFightError: 宠物相关错误
        """
        try:
            # 获取背包宠物列表
            self.send_packet_processing.SendPacket(
                '00 00 00 11 31 00 00 AA BA 00 00 00 00 00 00 00 00'
            )
            packet_data = self.receive_packet_analysis.wait_for_specific_data(
                43706, 
                timeout=self.battle_timeout
            )
            if not packet_data:
                raise PetFightError("获取背包宠物列表失败")

            # 解析背包数据
            packet_body = packet_data[17:]
            if packet_body == b'\x00\x00\x00\x00\x00\x00\x00\x00':
                self.logger.info("背包为空，检查仓库")
                return self.check_warehouse_pets(pet_ids)

            # 处理背包宠物
            self._process_backpack_pets(packet_body)
            
            # 检查仓库
            return self.check_warehouse_pets(pet_ids)

        except Exception as e:
            self.logger.error(f"检查背包宠物失败: {e}")
            return False

    def check_warehouse_pets(self, pet_ids: Tuple[int, ...]) -> bool:
        """检查仓库里是否有指定的宠物
        
        Args:
            pet_ids: 要检查的宠物ID元组
            
        Returns:
            bool: 是否找到所有宠物
            
        Raises:
            PetFightError: 宠物相关错误
        """
        try:
            # 获取仓库宠物列表
            self.send_packet_processing.SendPacket(
                '00 00 00 19 31 00 00 B1 E7 00 00 00 00 00 00 00 00 '
                '00 00 00 00 00 00 03 E7'
            )
            
            packet_data = self.receive_packet_analysis.wait_for_specific_data(
                45543,
                timeout=self.battle_timeout
            )
            if not packet_data:
                raise PetFightError("获取仓库宠物列表失败")

            # 检查每个宠物
            for pet_id in pet_ids:
                if not self._find_pet_in_warehouse(pet_id, packet_data):
                    self.logger.error(f"精灵 {pet_id} 未找到")
                    return False
                    
            return True

        except Exception as e:
            self.logger.error(f"检查仓库宠物失败: {e}")
            return False

    def prepare_battle(self, battle_type: str) -> bool:
        """准备战斗
        
        Args:
            battle_type: 战斗类型 ("84", "aggressive", "battlefield")
            
        Returns:
            bool: 是否准备成功
        """
        try:
            if self.is_fighting:
                raise PetFightError("已在战斗中")
                
            self.current_battle_type = battle_type
            self._prepare_battle_packets(battle_type)
            self.is_fighting = True
            return True
            
        except Exception as e:
            self.logger.error(f"准备战斗失败: {e}")
            return False

    def end_battle(self):
        """结束战斗"""
        self.is_fighting = False
        self.current_battle_type = None

    def execute_daily_tasks(self) -> bool:
        """执行日常任务
        
        Returns:
            bool: 是否全部成功
        """
        tasks = [
            (self.daily_props_collection, "日常道具收集"),
            (self.battery_dormant_switch, "电池休眠开关"),
            (self.fire_buffer, "火焰增益"),
            (self.experience_training_ground, "经验训练场"),
            (self.learning_training_ground, "学习训练场"),
            (self.trial_of_the_elf_king, "精灵王试炼"),
            (self.x_team_chamber, "X战队密室"),
            (self.titan_mines, "泰坦矿洞"),
        ]

        success = True
        for task, name in tasks:
            try:
                task()
                self.logger.info(f"{name} 完成")
                time.sleep(self.operation_delay)
            except Exception as e:
                self.logger.error(f"{name} 失败: {e}")
                success = False

        return success

    def _prepare_battle_packets(self, battle_type: str):
        """准备战斗数据包
        
        Args:
            battle_type: 战斗类型
            
        Raises:
            ValueError: 未知的战斗类型
        """
        if battle_type == "84":
            self.battle_packets = self._get_84_battle_packets()
        elif battle_type == "aggressive":
            self.battle_packets = self._get_aggressive_battle_packets()
        elif battle_type == "battlefield":
            self.battle_packets = self._get_battlefield_battle_packets()
        else:
            raise ValueError(f"未知的战斗类型: {battle_type}")

    def _get_84_battle_packets(self) -> List[str]:
        """获取84战斗类型的数据包"""
        return [
            # 载入战斗
            '00 00 00 11 31 00 00 09 64 00 00 00 00 00 00 00 00',
            # 首发表姐，使用守御八方
            '00 00 00 15 31 00 00 09 65 00 00 00 00 00 00 00 00 00 00 7B 11',
            # ... 其他数据包
        ]

    def _get_aggressive_battle_packets(self) -> List[str]:
        """获取强攻类型的数据包"""
        return [
            # 载入战斗
            '00 00 00 11 31 00 00 09 64 00 00 00 00 00 00 00 00',
            # ... 其他数据包
        ]

    def _get_battlefield_battle_packets(self) -> List[str]:
        """获取战场类型的数据包"""
        return [
            # 战场相关数据包
        ]

    def _process_backpack_pets(self, packet_body: bytes):
        """处理背包宠物数据
        
        Args:
            packet_body: 数据包主体
            
        Raises:
            PetFightError: 处理失败
        """
        try:
            # 获取宠物数量
            pet_count = int.from_bytes(packet_body[:4], byteorder='big')
            self.logger.info(f"背包宠物数量: {pet_count}")

            # 解析每个宠物的数据
            pet_data_start = 4
            pet_data_length = 390
            
            for i in range(pet_count):
                pet_data = packet_body[
                    pet_data_start:pet_data_start + pet_data_length
                ]
                
                # 提取宠物信息
                pet_id = int.from_bytes(pet_data[:4], byteorder='big')
                timestamp = int.from_bytes(
                    pet_data[148:152], 
                    byteorder='big'
                )
                
                # 缓存宠物信息
                self.pet_cache[pet_id] = PetInfo(
                    pet_id=pet_id,
                    timestamp=timestamp,
                    location="backpack"
                )
                
                self.logger.info(
                    f"背包精灵 {pet_id} 的时间戳: {timestamp}"
                )
                
                # 发送宠物数据包
                self._send_pet_packet(
                    timestamp.to_bytes(4, byteorder='big'), 
                    is_backpack=True
                )
                
                pet_data_start += pet_data_length

        except Exception as e:
            self.logger.error(f"处理背包宠物数据失败: {e}")
            raise PetFightError(f"处理背包宠物数据失败: {str(e)}")

    def daily_props_collection(self):
        """执行日常道具收集任务"""
        data = [
            # 星愿漂流瓶签到
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 01',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 02',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 03',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 04',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 05',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 06',
            '00 00 00 19 31 00 00 B8 BE 00 00 00 00 00 00 00 00 00 00 00 09 00 00 00 07',
            # 荣誉大厅军阶商店签到
            '00 00 00 19 31 00 00 A5 8C 00 00 00 00 00 00 00 00 00 00 00 04 00 00 00 04',
            # 勇者之塔扫荡
            '00 00 00 15 31 00 00 A2 EC 00 00 00 00 00 00 00 00 00 00 00 01',
            # 其他签到数据包...
        ]
        self._execute_packet_sequence(data)

    def battery_dormant_switch(self):
        """电池休眠开关"""
        self.send_packet_processing.SendPacket(
            '00 00 00 15 31 00 00 A0 CA 00 00 00 00 00 00 00 00 00 00 00 00'
        )

    def fire_buffer(self):
        """火焰增益"""
        data = [
            '00 00 00 15 31 00 00 10 C4 00 00 00 00 00 00 00 00 02 63 43 9C',
            '00 00 00 15 31 00 00 10 C4 00 00 00 00 00 00 00 00 02 2B F9 3F'
        ]
        self._execute_packet_sequence(data)

    def experience_training_ground(self):
        """经验训练场"""
        try:
            data = [
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 01',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 02',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 03',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 04',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 05',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 67 00 00 00 06 00 00 00 06'
            ]

            for _ in range(6):
                for packet in data:
                    self.send_packet_processing.SendPacket(packet)
                    time.sleep(self.operation_delay)
                    self._execute_battle_sequence("84")

            # 完成后的处理
            self.send_packet_processing.SendPacket(
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 67 '
                '00 00 00 03 00 00 00 00 00 00 00 00'
            )

        except Exception as e:
            self.logger.error(f"经验训练场失败: {e}")
            raise

    def _execute_battle_sequence(self, battle_type: str):
        """执行战斗序列
        
        Args:
            battle_type: 战斗类型
            
        Raises:
            PetFightError: 战斗失败
        """
        try:
            if not self.prepare_battle(battle_type):
                raise PetFightError("准备战斗失败")
                
            for packet in self.battle_packets:
                self.send_packet_processing.SendPacket(packet)
                time.sleep(self.operation_delay)
                
        except Exception as e:
            self.logger.error(f"执行战斗序列失败: {e}")
            raise PetFightError(f"执行战斗序列失败: {str(e)}")
        finally:
            self.end_battle()

    def _execute_packet_sequence(self, packets: List[str]):
        """执行数据包序列
        
        Args:
            packets: 数据包列表
            
        Raises:
            PetFightError: 执行失败
        """
        try:
            for packet in packets:
                self.send_packet_processing.SendPacket(packet)
                time.sleep(self.operation_delay)
        except Exception as e:
            self.logger.error(f"执行数据包序列失败: {e}")
            raise PetFightError(f"执行数据包序列失败: {str(e)}")

    def learning_training_ground(self):
        """学习力训练场"""
        try:
            data = [
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 06 00 00 00 01',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 06 00 00 00 02',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 06 00 00 00 03',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 06 00 00 00 04',
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 06 00 00 00 05'
            ]

            for _ in range(6):
                for packet in data:
                    self.send_packet_processing.SendPacket(packet)
                    time.sleep(self.operation_delay)
                    self._execute_battle_sequence("84")

            # 完成后的处理
            self.send_packet_processing.SendPacket(
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 66 '
                '00 00 00 03 00 00 00 00 00 00 00 00'
            )

        except Exception as e:
            self.logger.error(f"学习力训练场失败: {e}")
            raise PetFightError(f"学习力训练场失败: {str(e)}")

    def trial_of_the_elf_king(self):
        """精灵王试炼"""
        try:
            data = '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 6A 00 00 00 0F 00 00 00 03'

            for _ in range(15):
                self.send_packet_processing.SendPacket(data)
                time.sleep(self.operation_delay)
                self._execute_battle_sequence("84")

        except Exception as e:
            self.logger.error(f"精灵王试炼失败: {e}")
            raise PetFightError(f"精灵王试炼失败: {str(e)}")

    def x_team_chamber(self):
        """X战队密室"""
        try:
            data = [
                # 开启副本
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 69 00 00 00 01 00 00 00 01 00 00 00 00',
                # 开启挑战
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 69 00 00 00 07 00 00 00 00',
                # 通关奖励
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 69 00 00 00 02 00 00 00 00 00 00 00 00'
            ]

            for _ in range(3):
                self.send_packet_processing.SendPacket(data[0])
                time.sleep(self.operation_delay)
                
                self.send_packet_processing.SendPacket(data[1])
                time.sleep(self.operation_delay)
                
                self._execute_battle_sequence("84")

            # 领取奖励
            self.send_packet_processing.SendPacket(data[2])

        except Exception as e:
            self.logger.error(f"X战队密室失败: {e}")
            raise PetFightError(f"X战队密室失败: {str(e)}")

    def titan_mines(self):
        """泰坦���洞"""
        try:
            # 检查所需宠物
            pet_ids_needed = (3512, 3437, 3045)
            if not self.check_backpack_pets(pet_ids_needed):
                raise PetFightError("所需宠物不足")

            # 选择困难模式
            self.send_packet_processing.SendPacket(
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 68 '
                '00 00 00 01 00 00 00 03 00 00 00 00'
            )
            time.sleep(self.operation_delay)

            # 执行各个阶段
            self._execute_titan_mines_stages()

        except Exception as e:
            self.logger.error(f"泰坦矿洞失败: {e}")
            raise PetFightError(f"泰坦矿洞失败: {str(e)}")

    def _execute_titan_mines_stages(self):
        """执行泰坦矿洞的各个阶段"""
        try:
            # 第一阶段：打开通道，击败守卫
            self._execute_titan_mines_stage1()
            
            # 第二阶段：清扫矿区
            self._execute_titan_mines_stage2()
            
            # 第三阶段：矿洞开采
            self._execute_titan_mines_stage3()
            
            # 第四阶段：安全撤离
            self._execute_titan_mines_stage4()

        except Exception as e:
            raise PetFightError(f"执行泰坦矿洞阶段失败: {str(e)}")

    def _execute_titan_mines_stage1(self):
        """执行泰坦矿洞第一阶段"""
        try:
            self.send_packet_processing.SendPacket(
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 68 '
                '00 00 00 03 00 00 00 01'
            )
            time.sleep(self.operation_delay)
            self._execute_battle_sequence("84")

        except Exception as e:
            raise PetFightError(f"泰坦矿洞第一阶段失败: {str(e)}")

    def _execute_titan_mines_stage2(self):
        """执行泰坦矿洞第二阶段"""
        try:
            # 切换到艾欧
            pet_ids_needed = (3437, )
            if not self.check_backpack_pets(pet_ids_needed):
                raise PetFightError("缺少艾欧")

            # 执行16次清扫
            for _ in range(16):
                self.send_packet_processing.SendPacket(
                    '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 68 '
                    '00 00 00 03 00 00 00 02'
                )
                time.sleep(self.operation_delay)
                self._execute_battle_sequence("aggressive")

        except Exception as e:
            raise PetFightError(f"泰坦矿洞第二阶段失败: {str(e)}")

    def _execute_titan_mines_stage3(self):
        """执行泰坦矿洞第三阶段(矿洞开采)"""
        try:
            # 矿洞开采数据包序列
            mining_packets = [
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 68 00 00 00 02 00 00 00 02 00 00 00 00',
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 68 00 00 00 02 00 00 00 03 00 00 00 00',
                '00 00 00 21 31 00 00 A5 9B 00 00 00 00 00 00 00 00 00 00 00 68 00 00 00 02 00 00 00 04 00 00 00 00',
                # ... 更多开采点位的数据包
            ]

            # 执行开采序列
            for packet in mining_packets:
                self.send_packet_processing.SendPacket(packet)
                time.sleep(self.operation_delay)
                
                # 检查开采结果
                if not self._check_mining_result():
                    raise PetFightError("开采失败")

        except Exception as e:
            raise PetFightError(f"泰坦矿洞第三阶段失败: {str(e)}")

    def _execute_titan_mines_stage4(self):
        """执行泰坦矿洞第四阶段(安全撤离)"""
        try:
            # 检查所需宠物
            pet_ids_needed = (3512, 3437, 3045)
            if not self.check_backpack_pets(pet_ids_needed):
                raise PetFightError("缺少撤离所需宠物")

            # 发送撤离数据包
            self.send_packet_processing.SendPacket(
                '00 00 00 1D 31 00 00 A5 9C 00 00 00 00 00 00 00 00 00 00 00 68 '
                '00 00 00 03 00 00 00 04'
            )
            time.sleep(self.operation_delay)

            # 执行撤离战斗
            self._execute_battle_sequence("84")

        except Exception as e:
            raise PetFightError(f"泰坦矿洞第四阶段失败: {str(e)}")

    def _check_mining_result(self) -> bool:
        """检查矿物开采结果
        
        Returns:
            bool: 开采是否成功
        """
        try:
            # 等待开采结果响应
            response = self.receive_packet_analysis.wait_for_specific_data(
                45543,  # 开采结果命令ID
                timeout=self.battle_timeout
            )
            
            if not response:
                return False
                
            # 解析开采结果
            result = response[17]  # 假设结果在第17个字节
            return result == 1  # 1表示成功
            
        except Exception as e:
            self.logger.error(f"检查开采结果失败: {e}")
            return False

    def get_battle_status(self) -> dict:
        """获取当前战斗状态
        
        Returns:
            dict: 战斗状态信息
        """
        return {
            "is_fighting": self.is_fighting,
            "battle_type": self.current_battle_type,
            "pet_cache_count": len(self.pet_cache)
        }

    def clear_pet_cache(self):
        """清理宠物缓存"""
        self.pet_cache.clear()
        self.logger.info("宠物缓存已清理")

    def get_cached_pet_info(self, pet_id: int) -> Optional[PetInfo]:
        """获取缓存的宠物信息
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            Optional[PetInfo]: 宠物信息，不存在则返回None
        """
        return self.pet_cache.get(pet_id)

    def _validate_pet_id(self, pet_id: int) -> bool:
        """验证宠物ID是否有效
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            bool: ID是否有效
        """
        # 这里可以添加更多的验证逻辑
        return 1000 <= pet_id <= 9999

    def _format_packet(self, packet: str) -> str:
        """格式化数据包字符串
        
        Args:
            packet: 原始数据包字符串
            
        Returns:
            str: 格式化后的数据包字符串
        """
        # 移除空格并转换为大写
        return "".join(packet.split()).upper()

    def __str__(self) -> str:
        """返回对象的字符串表示"""
        return (
            f"PetFightPacketManager(fighting={self.is_fighting}, "
            f"battle_type={self.current_battle_type}, "
            f"cached_pets={len(self.pet_cache)})"
        )

    def __repr__(self) -> str:
        """返回对象的详细字符串表示"""
        return (
            f"PetFightPacketManager("
            f"send_packet_processing={self.send_packet_processing!r}, "
            f"receive_packet_analysis={self.receive_packet_analysis!r}, "
            f"battle_timeout={self.battle_timeout}, "
            f"operation_delay={self.operation_delay}, "
            f"is_fighting={self.is_fighting}, "
            f"battle_type={self.current_battle_type!r}, "
            f"pet_cache={self.pet_cache!r})"
        )

    def _find_pet_in_warehouse(self, pet_id: int, packet_data: bytes) -> bool:
        """在仓库数据中查找指定宠物
        
        Args:
            pet_id: 宠物ID
            packet_data: 仓库数据
            
        Returns:
            bool: 是否找到宠物
        """
        try:
            pet_id_hex = pet_id.to_bytes(4, byteorder='big').hex()
            
            for i in range(len(packet_data) - 8):
                current_id = packet_data[i:i+4]
                if current_id == bytes.fromhex(pet_id_hex):
                    timestamp = packet_data[i+4:i+8]
                    timestamp_int = int.from_bytes(timestamp, byteorder='big')
                    
                    # 缓存宠物信息
                    self.pet_cache[pet_id] = PetInfo(
                        pet_id=pet_id,
                        timestamp=timestamp_int,
                        location="warehouse"
                    )
                    
                    self.logger.info(
                        f"仓库精灵 {pet_id} 的时间戳: {timestamp_int}"
                    )
                    
                    # 发送宠物数据包
                    self._send_pet_packet(timestamp, is_backpack=False)
                    return True
                    
            return False

        except Exception as e:
            self.logger.error(f"查找仓库宠物失败: {e}")
            return False

    def _send_pet_packet(self, timestamp: bytes, is_backpack: bool):
        """发送宠物相关数据包
        
        Args:
            timestamp: 时间戳
            is_backpack: 是否在背包中
        """
        try:
            location_flag = "00" if is_backpack else "01"
            packet = (
                f"00 00 00 19 31 00 00 09 00 00 00 00 00 00 00 00 00"
                f"{timestamp.hex().upper()} 00 00 00 {location_flag}"
            )
            self.send_packet_processing.SendPacket(packet)
            time.sleep(self.operation_delay)
            
        except Exception as e:
            self.logger.error(f"发送宠物数据包失败: {e}")
            raise PetFightError(f"发送宠物数据包失败: {str(e)}")

    def switch_pet(self, pet_id: int) -> bool:
        """切换到指定宠物
        
        Args:
            pet_id: 要切换到的宠物ID
            
        Returns:
            bool: 是否切换成功
        """
        try:
            if not self._validate_pet_id(pet_id):
                raise PetFightError(f"无效的宠物ID: {pet_id}")
                
            # 检查宠物是否在缓存中
            pet_info = self.get_cached_pet_info(pet_id)
            if not pet_info:
                # 尝试在背包和仓库中查找
                if not self.check_backpack_pets((pet_id,)):
                    raise PetFightError(f"找不到宠物: {pet_id}")
                pet_info = self.get_cached_pet_info(pet_id)
                
            # 发送切换宠物数据包
            switch_packet = (
                f"00 00 00 15 31 00 00 09 67 00 00 00 00 00 00 00 00 "
                f"{pet_info.timestamp:08X}"
            )
            self.send_packet_processing.SendPacket(switch_packet)
            time.sleep(self.operation_delay)
            
            return True
            
        except Exception as e:
            self.logger.error(f"切换宠物失败: {e}")
            return False

    def heal_pets(self):
        """治疗所有宠物"""
        try:
            heal_packet = (
                '00 00 00 11 31 00 00 B8 20 00 00 00 00 00 00 00 00'
            )
            self.send_packet_processing.SendPacket(heal_packet)
            time.sleep(self.operation_delay)
            
        except Exception as e:
            self.logger.error(f"治疗宠物失败: {e}")
            raise PetFightError(f"治疗宠物失败: {str(e)}")

    def escape_battle(self):
        """从战斗中逃跑"""
        try:
            if not self.is_fighting:
                return
                
            escape_packet = (
                '00 00 00 11 31 00 00 09 6A 00 00 00 00 00 00 00 00'
            )
            self.send_packet_processing.SendPacket(escape_packet)
            time.sleep(self.operation_delay)
            
        except Exception as e:
            self.logger.error(f"逃跑失败: {e}")
        finally:
            self.end_battle()

    def validate_battle_requirements(self, battle_type: str, required_pets: Tuple[int, ...]) -> bool:
        """验证战斗要求
        
        Args:
            battle_type: 战斗类型
            required_pets: 所需宠物ID元组
            
        Returns:
            bool: 是否满足要求
        """
        try:
            # 检查战斗类型
            if battle_type not in ["84", "aggressive", "battlefield"]:
                raise PetFightError(f"无效的战斗类型: {battle_type}")
                
            # 检查是否已在战斗中
            if self.is_fighting:
                raise PetFightError("已在战斗中")
                
            # 检查所需宠物
            if required_pets and not self.check_backpack_pets(required_pets):
                raise PetFightError("缺少所需宠物")
                
            return True
            
        except Exception as e:
            self.logger.error(f"验证战斗要求失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            self.end_battle()
            self.clear_pet_cache()
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()