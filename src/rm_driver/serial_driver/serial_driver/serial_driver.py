import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from rm_interfaces.msg import Referee

import struct
import serial
from multiprocessing import Process, Queue
import time


TRANSMIT_RATE = 300
RECEIVE_RATE = 300

# 初始化串口
def init_serial() -> serial.Serial:
    ser = serial.Serial(
        port="/dev/ttyS0",
        baudrate=115200
    )
    print("打开串口")
    return ser

# CRC计算
def crc16(data_pack: list[int]) -> list[bytes]:
    crc = 0xFFFF # 初始化CRC校验值为0xFFFF
    for byte in data_pack:
        crc ^= byte # 将当前数据字节与CRC校验值进行异或运算
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001 # 使用CRC16多项式进行异或运算
            else:
                crc >>= 1
    return [bytes([byte]) for byte in struct.pack('H', crc)]

# 串口发送器
class Transmitter():
    def __init__(self, ser: serial.Serial, nav_pack_queue: Queue, aim_pack_queue: Queue) -> None:
        self.ser = ser
        self.nav_pack_queue: Queue = nav_pack_queue
        self.aim_pack_queue: Queue = aim_pack_queue
        self.last_nav_pack = None
        self.last_aim_pack = None

    def transmit(self):
        while True:
            time.sleep(1.0 / TRANSMIT_RATE)
            data_pack = [b'\x1A', b'\xA1', b'\x00', b'\x00']

            # 判断是否有导航数据
            if not self.nav_pack_queue.empty():
                self.last_nav_pack = self.nav_pack_queue.get() # 获取导航数据
            if not self.last_nav_pack is None:
                data_pack[2] = b'\xFF'
                data_pack.extend(bytes([byte]) for byte in self.last_nav_pack)
                while len(data_pack) < 36: # 添加预留空数据
                    data_pack.append(b'\x00')
                data_pack.extend(crc16(self.last_nav_pack)) # 添加CRC16校验位
            
            # 补全空余数据
            while len(data_pack) < 44:
                data_pack.append(b'\x00')

            # 判断是否有自瞄数据
            if not self.aim_pack_queue.empty():
                self.last_aim_pack = self.aim_pack_queue
            if not self.last_aim_pack is None:
                data_pack[3] = b'\xFF'

            # 补全空余数据
            while len(data_pack) < 64:
                data_pack.append(b'\x00')
            
            for data in data_pack:
                self.ser.write(data)
            

# 串口通信节点
class Serial_driver(Node):

    def __init__(self, name):
        super().__init__(name)

        # 接收导航速度数据
        self.twist_sub = self.create_subscription(Twist, '/cmd_vel', self.vel_callback, 10)

        # 发送导航数据
        self.referee_pub = self.create_publisher(Referee, "referee_data", 10)

        # 多进程实现串口同时读写
        self.nav_queue = Queue(maxsize=3)
        self.aim_queue = Queue(maxsize=3)
        
        self.ser = init_serial()
        
        self.transmitter = Transmitter(self.ser, self.nav_queue, self.aim_queue)
        transmit_process = Process(target=self.transmitter.transmit)
        transmit_process.start()

        # 串口接收计时器
        self.receive_timer = self.create_timer(1.0 / RECEIVE_RATE, self.receive_callback)

    # 导航数据接收回调
    def vel_callback(self, msg: Twist):
        int_x = int(msg.linear.x * 1000000000)
        int_y = int(msg.linear.y * 1000000000)

        data_pack = [i for i in struct.pack('i', int_x)]
        data_pack.extend([i for i in struct.pack('i', int_y)])
        
        if self.nav_queue.full():
            self.get_logger().warn("导航串口通信队列已满")
            return
        self.nav_queue.put(data_pack)
    
    # 串口接收计时器回调
    def receive_callback(self):
        if self.ser.read() != b'\x3A':
            return
        if self.ser.read() != b'\xA3':
            return
        
        # 获取其余所有数据
        data_pack: list[bytes] = []
        while len(data_pack) < 62:
            data = self.ser.read()
            data_pack.append(data)

        # 导航数据
        if data_pack[0] == b'\xff':
            nav_pack = data_pack[2:34]
            msg = Referee()
            msg.sentry_hp = struct.unpack('h', b''.join(nav_pack[0:2]))[0]
            msg.base_hp = struct.unpack('h', b''.join(nav_pack[2:4]))[0]
            msg.ammo = struct.unpack('h', b''.join(nav_pack[4:6]))[0]
            msg.remaining_time = struct.unpack('h', b''.join(nav_pack[6:8]))[0]
            self.referee_pub.publish(msg)
            
        # 自瞄数据
        if data_pack[1] == b'\xff':
            aim_pack = data_pack[42:58]
        

def main(args=None):
    rclpy.init(args=args)
    node = Serial_driver("serial_driver")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

