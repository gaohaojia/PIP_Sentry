import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8
from geometry_msgs.msg import Twist

import struct
import serial
import serial.tools.list_ports as stl
from multiprocessing import Process, Queue
import time

# 初始化串口
def init_serial() -> serial.Serial:
    ports_list = list(stl.comports())
    if len(ports_list) == 0:
        # 测试用虚拟串口
        ports_list.append("/dev/pts/3")
    
    ser = serial.Serial(
        port=ports_list[0],
        baudrate=115200
    )
    # ser = serial.Serial(
    #     port='/dev/pts/3',
    #     baudrate=115200
    # )
    print("打开串口")
    return ser

# crc计算
def crc16(data_pack: list[int]) -> bytes:
    crc = 0xFFFF # 初始化CRC校验值为0xFFFF
    for byte in data_pack:
        crc ^= byte # 将当前数据字节与CRC校验值进行异或运算
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001 # 使用CRC16多项式进行异或运算
            else:
                crc >>= 1
    return struct.pack('H', crc)

# 串口发送器
class Transmitter():
    def __init__(self, ser: serial.Serial, nav_queue: Queue, aim_queue: Queue) -> None:
        self.ser = ser
        self.nav_queue: Queue = nav_queue
        self.aim_queue: Queue = aim_queue

    def transmit(self):
        while True:
            time.sleep(0.001)
            data_pack = [b'\x1A', b'\xA1', b'\x00', b'\x00']

            # 判断是否有导航数据
            if not self.nav_queue.empty():
                data_pack[2] = b'\xFF'
                nav_data_pack = self.nav_queue.get() # 获取导航数据
                data_pack.extend(bytes([byte]) for byte in nav_data_pack)
                while len(data_pack) < 36: # 添加预留空数据
                    data_pack.append(b'\x00')
                data_pack.append(crc16(nav_data_pack)) # 添加CRC16校验位
            
            while len(data_pack) < 44:
                data_pack.append(b'\x00')

            if not self.aim_queue.empty():
                data_pack[3] = b'\xFF'
            while len(data_pack) < 63:
                data_pack.append(b'\x00')

            if data_pack[2] == b'\x00' and data_pack[3] == b'\x00':
                continue
            
            for data in data_pack:
                self.ser.write(data)
                

# 串口接受器
class Receiver():
    def __init__(self, ser: serial.Serial, nav_pub) -> None:
        self.ser = ser
        self.nav_pub = nav_pub

    def receive(self):
        while True:
            
            # 判断是否为头文件
            if self.ser.read() != b'\x3A':
                continue
            if self.ser.read() != b'\xA3':
                continue

            # 获取其余所有数据
            data_pack: list[bytes] = []
            while len(data_pack) < 62:
                data = self.ser.read()
                data_pack.append(data)

            # 校验尾数据
            if data_pack[62] != b'\x3B' or data_pack[63] != b'\xB3':
                continue

            # 导航数据
            if data_pack[0] == b'\xff':

                nav_pack = data_pack[8:40]
            
            # 自瞄数据
            if data_pack[1] == b'\xff':
                
                aim_pack = data_pack[44:60]
            

# 串口通信节点
class Serial_driver(Node):

    def __init__(self, name):
        super().__init__(name)

        # 接收导航速度数据
        self.twist_sub = self.create_subscription(Twist, '/cmd_vel', self.vel_callback, 10)

        # 发送导航数据
        self.nav_pub = self.create_publisher(Int8, "nav_msg", 10)

        self.nav_queue = Queue(maxsize=3)
        self.aim_queue = Queue(maxsize=3)
        
        self.ser = init_serial()
        self.transmitter = Transmitter(self.ser, self.nav_queue, self.aim_queue)
        self.receiver = Receiver(self.ser, self.nav_pub)

        process = [Process(target=self.receiver.receive),
                  Process(target=self.transmitter.transmit)]
        [p.start() for p in process]

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
        

def main(args=None):
    rclpy.init(args=args)
    node = Serial_driver("serial_driver")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
