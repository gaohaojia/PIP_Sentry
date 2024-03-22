import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8
from geometry_msgs.msg import Twist

import struct
import serial
import serial.tools.list_ports as stl
from multiprocessing import Process, Pipe

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

# 串口发送器
class Transmitter():
    def __init__(self, ser: serial.Serial) -> None:
        self.ser = ser

    def transmit(self, data_pack: list[bytes]):
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
        
        self.ser = init_serial()
        self.transmitter = Transmitter(self.ser)
        self.receiver = Receiver(self.ser, self.nav_pub)

        recv_p = Process(target=self.receiver.receive, args=( ))
        recv_p.start()

    # 导航数据接收回调
    def vel_callback(self, msg: Twist):
        int_x = int(msg.linear.x * 1000000000)
        int_y = int(msg.linear.y * 1000000000)

        data_pack = [b'\x1A', b'\xA1', b'\xB1', b'\x00']
        data_pack.append(struct.pack('i', int_x))
        data_pack.append(struct.pack('i', int_y))
        while len(data_pack) < 58:
            data_pack.append(b'\x00')

        self.transmitter.transmit(data_pack)
        # self.get_logger().info(f"x:{msg.linear.x}, y:{msg.linear.y}")

def main(args=None):
    rclpy.init(args=args)
    node = Serial_driver("serial_driver")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
