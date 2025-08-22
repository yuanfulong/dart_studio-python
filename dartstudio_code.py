#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART Studio服务器端实现 - 真实Doosan机械臂版本
========================================
此文件需要保存为 doosan_robot_server.drtl 并在DART Studio中运行
"""

import socket
import threading
import json
import time
import sys
from typing import Dict, Any, List, Optional

# DART Studio环境中的真实API导入
# 根据您的DART Studio版本调整导入
try:
    # Doosan Robot API - 根据实际DART Studio版本调整
    from dsr_python import *

    DART_STUDIO_AVAILABLE = True
    print("✅ DART Studio robot API loaded successfully")
except ImportError:
    print("❌ DART Studio robot API not available - running in simulation mode")
    DART_STUDIO_AVAILABLE = False

# 服务器配置
DEFAULT_HOST = "0.0.0.0"  # 监听所有接口
DEFAULT_PORT = 9000
DEFAULT_TOKEN = "TEST_TOKEN_123"

# Doosan机械臂配置 - 根据您的实际机械臂IP修改
ROBOT_IP = "192.168.1.100"  # 修改为您的机械臂实际IP
ROBOT_NAME = "dsr01"  # 机械臂名称


class DoosanRobotController:
    """真实Doosan机械臂控制器"""

    def __init__(self):
        self.robot = None
        self.initialized = False
        self.current_joints = [0.0] * 6
        self.current_pose = [0.0] * 6

    def initialize_robot(self):
        """初始化机械臂连接"""
        try:
            if not DART_STUDIO_AVAILABLE:
                print("⚠️  DART Studio API not available, using simulation")
                return False

            # 初始化机械臂
            # 根据您的DART Studio版本调整这些调用
            print(f"🔌 Connecting to Doosan robot at {ROBOT_IP}...")

            # 设置机械臂IP和名称
            set_robot_ip(ROBOT_IP)
            set_robot_name(ROBOT_NAME)

            # 连接机械臂
            if not connect_robot():
                print(f"❌ Failed to connect to robot at {ROBOT_IP}")
                return False

            print("✅ Robot connected successfully")

            # 设置机械臂模式
            set_robot_mode(ROBOT_MODE_MANUAL)  # 手动模式

            # 等待机械臂准备就绪
            time.sleep(1)

            # 获取初始状态
            self.update_robot_state()

            self.initialized = True
            print("🤖 Doosan robot initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Robot initialization failed: {e}")
            return False

    def update_robot_state(self):
        """更新机械臂状态"""
        try:
            if self.initialized:
                self.current_joints = get_current_joint()
                self.current_pose = get_current_pos()
        except Exception as e:
            print(f"⚠️  Failed to update robot state: {e}")

    def move_joint(self, positions, speed):
        """关节运动"""
        try:
            if not self.initialized:
                return False

            # 转换速度格式 (DART Studio使用不同的速度单位)
            vel = speed * 100  # 转换为度/秒
            acc = vel * 2  # 加速度通常是速度的2倍

            # 执行关节运动
            movej(positions, vel=vel, acc=acc)

            # 等待运动完成
            wait_motion_done()

            # 更新状态
            self.update_robot_state()
            return True

        except Exception as e:
            print(f"❌ MoveJ failed: {e}")
            return False

    def move_linear(self, positions, speed):
        """直线运动"""
        try:
            if not self.initialized:
                return False

            # 转换速度和位置格式
            vel = speed * 100  # mm/s
            acc = vel * 2  # mm/s²

            # 执行直线运动
            movel(positions, vel=vel, acc=acc)

            # 等待运动完成
            wait_motion_done()

            # 更新状态
            self.update_robot_state()
            return True

        except Exception as e:
            print(f"❌ MoveL failed: {e}")
            return False

    def set_digital_output(self, pin, value):
        """设置数字输出"""
        try:
            if not self.initialized:
                return False

            # Doosan的数字输出控制
            set_digital_output(pin, value)
            return True

        except Exception as e:
            print(f"❌ SetDO failed: {e}")
            return False

    def get_digital_input(self, pin):
        """获取数字输入"""
        try:
            if not self.initialized:
                return False

            return get_digital_input(pin)

        except Exception as e:
            print(f"❌ GetDI failed: {e}")
            return False

    def emergency_stop(self):
        """紧急停止"""
        try:
            if self.initialized:
                stop_robot()  # 或使用 emergency_stop() 根据API版本
            return True
        except Exception as e:
            print(f"❌ Emergency stop failed: {e}")
            return False

    def reset_robot(self):
        """复位机械臂"""
        try:
            if self.initialized:
                # 根据您的DART Studio版本调整
                reset_robot_error()
                time.sleep(1)
                self.update_robot_state()
            return True
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return False

    def get_robot_state(self):
        """获取机械臂状态"""
        try:
            if not self.initialized:
                return {"state": "NOT_INITIALIZED"}

            self.update_robot_state()

            # 获取机械臂状态信息
            state_info = {
                "robot_state": "READY" if self.initialized else "ERROR",
                "current_joints": self.current_joints,
                "current_pose": self.current_pose,
                "is_moving": is_robot_moving() if self.initialized else False,
                "is_ready": not is_robot_moving() if self.initialized else False,
            }

            return state_info

        except Exception as e:
            print(f"❌ Get robot state failed: {e}")
            return {"state": "ERROR", "error": str(e)}


class DartStudioServer:
    """DART Studio TCP服务器"""

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=DEFAULT_TOKEN):
        self.host = host
        self.port = port
        self.token = token
        self.server_socket = None
        self.running = False
        self.clients = []

        # 初始化机械臂控制器
        self.robot_controller = DoosanRobotController()

    def start_server(self):
        """启动服务器"""
        try:
            # 首先初始化机械臂
            print("🤖 Initializing Doosan robot...")
            if not self.robot_controller.initialize_robot():
                print("⚠️  Robot initialization failed, but server will continue")

            # 启动TCP服务器
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"🚀 DART Studio Server started on {self.host}:{self.port}")
            print(f"🔑 Token: {self.token}")
            print(f"🤖 Robot IP: {ROBOT_IP}")
            print("⏳ Waiting for Python client connections...")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"🔌 New connection from {address}")

                    # 在单独线程中处理客户端
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        print(f"❌ Socket error: {e}")

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 Server stopped")

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        authenticated = False

        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break

                try:
                    message = json.loads(data.decode('utf-8').strip())
                    print(f"📨 Received from {address}: {message}")

                    # 处理消息
                    response = self.process_message(message, authenticated)

                    # 更新认证状态
                    if message.get('type') == 'auth' and response.get('status') == 'ok':
                        authenticated = True

                    # 发送响应
                    response_data = json.dumps(response) + "\n"
                    client_socket.send(response_data.encode('utf-8'))
                    print(f"📤 Sent to {address}: {response}")

                except json.JSONDecodeError as e:
                    error_response = {"status": "error", "message": f"Invalid JSON: {e}"}
                    client_socket.send((json.dumps(error_response) + "\n").encode('utf-8'))
                except Exception as e:
                    error_response = {"status": "error", "message": f"Processing error: {e}"}
                    client_socket.send((json.dumps(error_response) + "\n").encode('utf-8'))

        except Exception as e:
            print(f"❌ Client {address} error: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Client {address} disconnected")

    def process_message(self, message: Dict[str, Any], authenticated: bool) -> Dict[str, Any]:
        """处理消息"""
        msg_type = message.get('type')
        token = message.get('token')

        # 验证Token
        if token != self.token:
            return {"status": "error", "message": "Invalid token"}

        # 处理认证
        if msg_type == 'auth':
            return {"status": "ok", "message": "Authentication successful"}

        # 其他命令需要认证
        if not authenticated and msg_type != 'ping':
            return {"status": "error", "message": "Authentication required"}

        # 处理不同消息类型
        if msg_type == 'ping':
            return {"status": "ok", "pong": True}
        elif msg_type == 'call':
            return self.handle_function_call(message)
        elif msg_type == 'sequence':
            return self.handle_sequence(message)
        else:
            return {"status": "error", "message": f"Unknown message type: {msg_type}"}

    def handle_function_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理函数调用"""
        function = message.get('function')
        args = message.get('args', {})

        print(f"🤖 Executing function: {function} with args: {args}")

        try:
            if function == "MoveJ":
                return self.execute_move_j(args)
            elif function == "MoveL":
                return self.execute_move_l(args)
            elif function == "SetDO":
                return self.execute_set_do(args)
            elif function == "GetDI":
                return self.execute_get_di(args)
            elif function == "WaitMs":
                return self.execute_wait_ms(args)
            elif function == "GetCurrentPose":
                return self.execute_get_current_pose(args)
            elif function == "GetJointAngles":
                return self.execute_get_joint_angles(args)
            elif function == "EmergencyStop":
                return self.execute_emergency_stop(args)
            elif function == "ResetRobot":
                return self.execute_reset_robot(args)
            elif function == "GetRobotState":
                return self.execute_get_robot_state(args)
            else:
                return {"status": "error", "message": f"Unknown function: {function}"}

        except Exception as e:
            return {"status": "error", "message": f"Function execution error: {e}"}

    def handle_sequence(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理命令序列"""
        commands = message.get('commands', [])
        results = []

        for i, command in enumerate(commands):
            print(f"🔄 Executing command {i + 1}/{len(commands)}: {command}")
            result = self.handle_function_call(command)
            results.append(result)

            if result.get('status') != 'ok':
                break

        return {
            "status": "ok",
            "total_commands": len(commands),
            "executed_commands": len(results),
            "results": results
        }

    # 机械臂函数实现
    def execute_move_j(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行关节运动"""
        positions = args.get('positions', [])
        speed = args.get('speed', 0.2)

        if len(positions) != 6:
            return {"status": "error", "message": "MoveJ requires 6 joint positions"}

        try:
            success = self.robot_controller.move_joint(positions, speed)
            if success:
                return {
                    "status": "ok",
                    "message": "MoveJ completed",
                    "positions": positions,
                    "speed": speed
                }
            else:
                return {"status": "error", "message": "MoveJ failed"}
        except Exception as e:
            return {"status": "error", "message": f"MoveJ error: {e}"}

    def execute_move_l(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行直线运动"""
        positions = args.get('positions', [])
        speed = args.get('speed', 0.2)

        if len(positions) != 6:
            return {"status": "error", "message": "MoveL requires 6 pose values"}

        try:
            success = self.robot_controller.move_linear(positions, speed)
            if success:
                return {
                    "status": "ok",
                    "message": "MoveL completed",
                    "positions": positions,
                    "speed": speed
                }
            else:
                return {"status": "error", "message": "MoveL failed"}
        except Exception as e:
            return {"status": "error", "message": f"MoveL error: {e}"}

    def execute_set_do(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """设置数字输出"""
        pin = args.get('pin')
        value = args.get('value')

        if pin is None or value is None:
            return {"status": "error", "message": "SetDO requires pin and value"}

        try:
            success = self.robot_controller.set_digital_output(pin, value)
            if success:
                return {
                    "status": "ok",
                    "message": f"DO{pin} set to {value}",
                    "pin": pin,
                    "value": value
                }
            else:
                return {"status": "error", "message": f"Failed to set DO{pin}"}
        except Exception as e:
            return {"status": "error", "message": f"SetDO error: {e}"}

    def execute_get_di(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取数字输入"""
        pin = args.get('pin')

        if pin is None:
            return {"status": "error", "message": "GetDI requires pin"}

        try:
            value = self.robot_controller.get_digital_input(pin)
            return {
                "status": "ok",
                "pin": pin,
                "value": value
            }
        except Exception as e:
            return {"status": "error", "message": f"GetDI error: {e}"}

    def execute_wait_ms(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """等待毫秒"""
        ms = args.get('ms', 0)

        try:
            time.sleep(ms / 1000.0)
            return {
                "status": "ok",
                "message": f"Waited {ms}ms"
            }
        except Exception as e:
            return {"status": "error", "message": f"Wait error: {e}"}

    def execute_get_current_pose(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取当前位姿"""
        try:
            self.robot_controller.update_robot_state()
            return {
                "status": "ok",
                "pose": self.robot_controller.current_pose
            }
        except Exception as e:
            return {"status": "error", "message": f"GetCurrentPose error: {e}"}

    def execute_get_joint_angles(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取当前关节角度"""
        try:
            self.robot_controller.update_robot_state()
            return {
                "status": "ok",
                "joints": self.robot_controller.current_joints
            }
        except Exception as e:
            return {"status": "error", "message": f"GetJointAngles error: {e}"}

    def execute_emergency_stop(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """紧急停止"""
        try:
            success = self.robot_controller.emergency_stop()
            if success:
                return {
                    "status": "ok",
                    "message": "Emergency stop executed"
                }
            else:
                return {"status": "error", "message": "Emergency stop failed"}
        except Exception as e:
            return {"status": "error", "message": f"Emergency stop error: {e}"}

    def execute_reset_robot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """复位机械臂"""
        try:
            success = self.robot_controller.reset_robot()
            if success:
                return {
                    "status": "ok",
                    "message": "Robot reset completed"
                }
            else:
                return {"status": "error", "message": "Robot reset failed"}
        except Exception as e:
            return {"status": "error", "message": f"Reset error: {e}"}

    def execute_get_robot_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取机械臂状态"""
        try:
            state = self.robot_controller.get_robot_state()
            return {
                "status": "ok",
                "robot_state": state
            }
        except Exception as e:
            return {"status": "error", "message": f"GetRobotState error: {e}"}


def main():
    """主函数"""
    print("🤖 DART Studio Server for Doosan Robot")
    print("=" * 50)

    # 从这里修改您的机械臂IP地址
    global ROBOT_IP
    ROBOT_IP = "192.168.1.100"  # 修改为您的机械臂实际IP

    print(f"🔧 Robot IP: {ROBOT_IP}")
    print(f"🔧 Server Port: {DEFAULT_PORT}")
    print(f"🔧 Token: {DEFAULT_TOKEN}")

    # 创建并启动服务器
    server = DartStudioServer()

    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nℹ️  Server interrupted by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        server.stop_server()


if __name__ == "__main__":
    main()