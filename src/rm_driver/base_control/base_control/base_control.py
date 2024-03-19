import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

try:
    import serial
except:
    pass

last_time = time.time()
now_time = time.time()

class BaseControl(Node):

    def __init__(self, name):
        super().__init__(name)
        self.twist_sub = self.create_subscription(Twist, '/cmd_vel', self.vel_callback, 10)
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200)
        except:
            pass

    def vel_callback(self, msg):
        global now_time, last_time
        now_time = time.time()
        self.get_logger().info(f"当前帧数:{1 / (now_time - last_time)}")
        last_time = now_time
        cmd = [0x45, str(msg.linear.x).encode(), str(msg.linear.y).encode()]
        try:
            self.ser.write(cmd)
        except:
            pass
        # self.get_logger().info(f"x:{msg.linear.x}, y:{msg.linear.y}")

def main(args=None):
    rclpy.init(args=args)
    node = BaseControl("base_control")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
