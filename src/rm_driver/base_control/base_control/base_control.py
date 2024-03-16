import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial

class BaseControl(Node):

    def __init__(self, name):
        super().__init__(name)
        self.twist_sub = self.create_subscription(Twist, '/cmd_vel', self.vel_callback, 10)
        self.ser = serial.Serial('/dev/ttyUSB0', 115200)

    def vel_callback(self, msg):
        cmd = [0x45, str(msg.linear.x).encode(), str(msg.linear.y).encode()]
        self.ser.write(cmd)
        # self.get_logger().info(f"x:{msg.linear.x}, y:{msg.linear.y}")

def main(args=None):
    rclpy.init(args=args)
    node = BaseControl("base_control")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
