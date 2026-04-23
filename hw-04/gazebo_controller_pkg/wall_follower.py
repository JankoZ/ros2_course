#!/usr/bin/env python3

import rclpy
import math

from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.qos import QoSProfile, ReliabilityPolicy

class WallFollower(Node):
    def __init__(self):
        super().__init__("wall_follower")
        
        qos = QoSProfile(depth = 10, reliability = ReliabilityPolicy.BEST_EFFORT)
        
        self.sub_scan = self.create_subscription(LaserScan, "/scan", self.scan_callback, qos)
        self.sub_odom = self.create_subscription(Odometry, "/odom", self.odom_callback, 10)
        self.pub_vel = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        
        self.state = "FIND_WALL"
        self.ranges = []
        self.dist_wall = 0.5
        
        self.path_file = open("trajectory.txt", 'w')
        self.create_timer(0.1, self.control_loop)
        self.get_logger().info("--- Wall Follower Started ---")

    def scan_callback(self, msg):
        self.ranges = [r if (not math.isinf(r) and not math.isnan(r)) else 3.5 for r in msg.ranges]

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.path_file.write(f"{x:.4f} {y:.4f}\n")

    def control_loop(self):
        if not self.ranges or len(self.ranges) < 360:
            return

        front = min(min(self.ranges[0:15] + self.ranges[345:359]), 10.0)
        right = min(self.ranges[260:280])
        front_right = min(self.ranges[310:330])
        
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"

        if self.state == "FIND_WALL":
            if front > self.dist_wall:
                cmd.twist.linear.x = 0.15
                cmd.twist.angular.z = 0.0
            else:
                self.get_logger().info("Wall found! Transition to TURN")
                self.state = "TURN"

        elif self.state == "TURN":
            if front < self.dist_wall * 1.5:
                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = 0.4
            else:
                self.get_logger().info("Front clear! Transition to FOLLOW")
                self.state = "FOLLOW"

        elif self.state == "FOLLOW":
            if front < self.dist_wall * 0.8:
                self.state = "TURN"
            
            elif right > 1.0: 
                cmd.twist.linear.x = 0.12
                cmd.twist.angular.z = -0.5
            else:
                cmd.twist.linear.x = 0.15
                error = right - self.dist_wall
                cmd.twist.angular.z = -(error * 2.2) 
                
                if front_right < self.dist_wall:
                    cmd.twist.angular.z = 0.3

        cmd.twist.angular.z = max(min(cmd.twist.angular.z, 0.8), -0.8)

        self.pub_vel.publish(cmd)

    def __del__(self):
        if hasattr(self, "path_file"):
            self.path_file.close()

def main():
    rclpy.init()
    node = WallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
    