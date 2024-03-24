import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# 导航类
class NavToPose():
    def __init__(self) -> None:
        self.navigator = BasicNavigator()
        self.navigator.waitUntilNav2Active()

        self.goal_pose = PoseStamped()
        self.goal_pose.header.frame_id = 'map'
        self.goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()

    # 设定导航任务
    def go2pose(self, x: float, y: float):
        self.goal_pose.pose.position.x = x
        self.goal_pose.pose.position.y = y
        self.navigator.goToPose(self.goal_pose)
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()

            # 误差小于0.1时结束导航
            if feedback.distance_remaining < 0.1:
                self.navigator.cancelTask()
                
            # 超时结束导航
            if Duration.from_msg(feedback.navigation_time) > Duration(seconds=60.0):
                self.navigator.cancelTask()
    
    # 终止导航任务
    def cancel(self):
        self.navigator.cancelTask()
            
# 决策树节点
class Decision_tree(Node):
    def __init__(self, name):
        super().__init__(name)


def main(args=None):
    rclpy.init(args=args)
    node = Decision_tree("decision_tree")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
