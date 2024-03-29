import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

from rm_interfaces.msg import Referee

# 导航类
class Nav2Pose():
    def __init__(self):
        self.navigator = BasicNavigator()
        self.navigator.waitUntilNav2Active()

        self.goal_pose = PoseStamped()
        self.goal_pose.header.frame_id = 'map'
        self.goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()

        self.navigator.setInitialPose(self.goal_pose)

    # 导航到目标点
    def go2pose(self, x, y):
        self.goal_pose.pose.position.x = x
        self.goal_pose.pose.position.y = y
        self.navigator.goToPose(self.goal_pose)
    
    # 终止导航任务
    def cancel(self):
        self.navigator.cancelTask()
            
# 决策树节点
class Decision_tree(Node):
    def __init__(self, name) -> None:
        super().__init__(name)

        self.nav2pose = Nav2Pose()
        
        # 裁判系统数据订阅
        self.referee_sub = self.create_subscription(Referee, 'referee_data', self.referee_callback, 10)

        self.get_logger().info("\n\n\n\n\n\n\n\n加载完成！\n\n\n\n\n\n\n\n")

        # 测试计时器
        self.test_timer = self.create_timer(3, self.test_callback)
        self.test_para = 1

        self.nav_feedback_timer = self.create_timer(0.001, self.nav_feedback_callback)

    # 裁判数据接收回调
    def referee_callback(self, msg):
        self.get_logger().info(f'哨兵血量:{msg.sentry_hp}，基地血量:{msg.base_hp}，发弹量:{msg.ammo}，剩余时间:{msg.remaining_time}')

    # 测试计时器
    def test_callback(self):
        self.nav2pose.go2pose(-1.0 * self.test_para, 1.0 * self.test_para)
        self.test_para *= -1

    # 持续导航函数
    def nav_feedback_callback(self):
        feedback = self.nav2pose.navigator.getFeedback()

        # 判断导航任务是否存在
        if feedback is None:
            return
        
        # 判断导航任务是否完成
        if self.nav2pose.navigator.isTaskComplete():
            return

        # 误差小于0.1时结束导航
        if feedback.distance_remaining < 0.1:
            self.nav2pose.navigator.cancelTask()
            return
            
        # 超时结束导航
        if Duration.from_msg(feedback.navigation_time) > Duration(seconds=1):
            self.nav2pose.navigator.cancelTask()
            return


def main(args=None):
    rclpy.init(args=args)
    node = Decision_tree("decision_tree")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
