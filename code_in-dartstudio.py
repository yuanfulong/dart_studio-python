#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART Studio服务器端实现 / DART Studio 서버 측 구현 / DART Studio Server Implementation
==================================================================================

作用 / 역할 / Purpose:
----------------------
这是运行在DART Studio环境中的TCP服务器，负责：
1. 接收来自Python客户端的控制指令
2. 将指令转换为Doosan机器人控制命令
3. 执行实际的机器人动作
4. 返回执行结果给Python客户端

이 프로그램은 DART Studio 환경에서 실행되는 TCP 서버로서 다음 역할을 담당합니다:
1. Python 클라이언트로부터 제어 명령 수신
2. 명령을 Doosan 로봇 제어 명령으로 변환
3. 실제 로봇 동작 실행
4. 실행 결과를 Python 클라이언트에 반환

This is a TCP server running in DART Studio environment, responsible for:
1. Receiving control commands from Python clients
2. Converting commands to Doosan robot control commands
3. Executing actual robot movements
4. Returning execution results to Python clients

系统架构 / 시스템 아키텍처 / System Architecture:
----------------------
Python Client (dart_link.py)
    ↓ TCP Socket Communication
DART Studio Server (code_in-dartstudio.py)
    ↓ Robot API Calls
Doosan Robot Hardware

使用方式 / 사용 방법 / Usage:
----------------------
1. 在DART Studio环境中运行此脚本 / DART Studio 환경에서 이 스크립트 실행 / Run this script in DART Studio environment
2. 服务器将监听端口9000等待连接 / 서버는 포트 9000에서 연결을 대기합니다 / Server will listen on port 9000 for connections
3. Python客户端通过dart_link.py连接并发送命令 / Python 클라이언트는 dart_link.py를 통해 연결하고 명령을 전송합니다 / Python clients connect and send commands via dart_link.py

支持的消息类型 / 지원되는 메시지 유형 / Supported Message Types:
----------------------
- 'auth': 认证消息 / 인증 메시지 / Authentication message
- 'ping': 连接测试 / 연결 테스트 / Connection test
- 'call': 单个函数调用 / 단일 함수 호출 / Single function call
- 'sequence': 命令序列 / 명령 시퀀스 / Command sequence

支持的机器人函数 / 지원되는 로봇 함수 / Supported Robot Functions:
----------------------
- MoveJ: 关节空间移动 / 관절 공간 이동 / Joint space movement
- MoveL: 直线移动 / 직선 이동 / Linear movement
- SetDO: 设置数字输出 / 디지털 출력 설정 / Set digital output
- GetDI: 获取数字输入 / 디지털 입력 가져오기 / Get digital input
- GetCurrentPose: 获取当前位姿 / 현재 자세 가져오기 / Get current pose
- GetJointAngles: 获取关节角度 / 관절 각도 가져오기 / Get joint angles
- EmergencyStop: 紧急停止 / 비상 정지 / Emergency stop
- ResetRobot: 机器人复位 / 로봇 리셋 / Robot reset
- GetRobotState: 获取机器人状态 / 로봇 상태 가져오기 / Get robot state
- WaitMs: 等待毫秒 / 밀리초 대기 / Wait milliseconds

安全特性 / 안전 기능 / Safety Features:
----------------------
- 令牌认证 / 토큰 인증 / Token authentication
- 异常处理 / 예외 처리 / Exception handling
- 紧急停止功能 / 비상 정지 기능 / Emergency stop functionality
- 连接管理 / 연결 관리 / Connection management

注意事项 / 주의사항 / Important Notes:
----------------------
1. 此脚本需要在连接Doosan机器人的DART Studio环境中运行
2. 需要根据实际机器人型号调整机器人初始化代码
3. 在生产环境中使用前请确保安全参数设置正确

1. 이 스크립트는 Doosan 로봇이 연결된 DART Studio 환경에서 실행되어야 합니다
2. 실제 로봇 모델에 따라 로봇 초기화 코드를 조정해야 합니다
3. 프로덕션 환경에서 사용하기 전에 안전 매개변수가 올바르게 설정되었는지 확인하세요

1. This script must be run in DART Studio environment with Doosan robot connected
2. Robot initialization code needs to be adjusted according to actual robot model
3. Please ensure safety parameters are correctly set before using in production environment
"""

import socket
import threading
import json
import time
import sys
from typing import Dict, Any, List, Optional

# DART Studio Robot API imports (these would be available in DART Studio environment)
# DART Studio 로봇 API 가져오기 (DART Studio 환경에서 사용 가능)
# DART Studio Robot API导入 (在DART Studio环境中可用)
try:
    # These are placeholders for DART Studio's actual robot API
    # 이것들은 DART Studio의 실제 로봇 API를 위한 플레이스홀더입니다
    # 这些是DART Studio实际机器人API的占位符
    # In real DART Studio environment, you would import actual robot control modules
    # 실제 DART Studio 환경에서는 실제 로봇 제어 모듈을 가져와야 합니다
    # 在真实的DART Studio环境中，您需要导入实际的机器人控制模块
    from dsr_robot import Robot, RobotMode, RobotState
    from dsr_msgs.msg import RobotError

    DART_STUDIO_AVAILABLE = True
except ImportError:
    # For testing outside DART Studio environment
    # DART Studio 환경 외부에서 테스트하기 위한 설정
    # 用于在DART Studio环境外进行测试
    print("Warning: DART Studio robot API not available. Running in simulation mode.")
    print("경고: DART Studio 로봇 API를 사용할 수 없습니다. 시뮬레이션 모드로 실행합니다.")
    print("警告：DART Studio机器人API不可用。以仿真模式运行。")
    DART_STUDIO_AVAILABLE = False

# Server Configuration / 서버 구성 / 服务器配置
DEFAULT_HOST = "0.0.0.0"  # Listen on all interfaces / 모든 인터페이스에서 수신 / 监听所有接口
DEFAULT_PORT = 9000
DEFAULT_TOKEN = "TEST_TOKEN_123"  # Should match client token / 클라이언트 토큰과 일치해야 함 / 应与客户端令牌匹配


class RobotSimulator:
    """机器人仿真器，用于无实际机器人的测试 / 실제 로봇 없이 테스트를 위한 로봇 시뮬레이터 / Robot simulator for testing without actual robot"""

    def __init__(self):
        self.current_joints = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.current_pose = [400.0, 0.0, 300.0, 0.0, 0.0, 0.0]  # [x,y,z,rx,ry,rz]
        self.digital_outputs = {}
        self.robot_state = "IDLE"

    def movej(self, positions, speed):
        """模拟关节移动 / 관절 이동 시뮬레이션 / Simulate joint movement"""
        print(f"[SIM] MoveJ to {positions} at speed {speed}")
        print(f"[시뮬] MoveJ {positions} 위치로 속도 {speed}로 이동")
        print(f"[仿真] MoveJ移动到{positions}，速度{speed}")
        self.current_joints = positions.copy()
        time.sleep(1)  # Simulate movement time / 이동 시간 시뮬레이션 / 模拟移动时间
        return True

    def movel(self, positions, speed):
        """模拟直线移动 / 직선 이동 시뮬레이션 / Simulate linear movement"""
        print(f"[SIM] MoveL to {positions} at speed {speed}")
        print(f"[시뮬] MoveL {positions} 위치로 속도 {speed}로 이동")
        print(f"[仿真] MoveL移动到{positions}，速度{speed}")
        self.current_pose = positions.copy()
        time.sleep(1)  # Simulate movement time / 이동 시간 시뮬레이션 / 模拟移动时间
        return True

    def set_digital_output(self, pin, value):
        """模拟数字输出 / 디지털 출력 시뮬레이션 / Simulate digital output"""
        print(f"[SIM] Set DO{pin} = {value}")
        print(f"[시뮬] DO{pin} = {value} 설정")
        print(f"[仿真] 设置DO{pin} = {value}")
        self.digital_outputs[pin] = value
        return True

    def get_digital_input(self, pin):
        """模拟数字输入 / 디지털 입력 시뮬레이션 / Simulate digital input"""
        # Return False for all inputs in simulation
        # 시뮬레이션에서 모든 입력에 대해 False 반환
        # 在仿真中所有输入返回False
        return False

    def emergency_stop(self):
        """模拟紧急停止 / 비상 정지 시뮬레이션 / Simulate emergency stop"""
        print("[SIM] EMERGENCY STOP!")
        print("[시뮬] 비상 정지!")
        print("[仿真] 紧急停止!")
        self.robot_state = "EMERGENCY_STOPPED"
        return True

    def reset_robot(self):
        """模拟机器人复位 / 로봇 리셋 시뮬레이션 / Simulate robot reset"""
        print("[SIM] Robot Reset")
        print("[시뮬] 로봇 리셋")
        print("[仿真] 机器人复位")
        self.robot_state = "IDLE"
        return True


class DartStudioServer:
    """DART Studio TCP服务器，用于机器人通信 / 로봇 통신을 위한 DART Studio TCP 서버 / DART Studio TCP Server for robot communication"""

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=DEFAULT_TOKEN):
        self.host = host
        self.port = port
        self.token = token
        self.server_socket = None
        self.running = False
        self.clients = []

        # Initialize robot interface / 로봇 인터페이스 초기화 / 初始化机器人接口
        if DART_STUDIO_AVAILABLE:
            try:
                # Initialize actual Doosan robot / 실제 Doosan 로봇 초기화 / 初始化实际的Doosan机器人
                self.robot = Robot()  # This would be the actual DART Studio robot object / 실제 DART Studio 로봇 객체 / 这将是实际的DART Studio机器人对象
                print("✅ Doosan robot initialized")
                print("✅ Doosan 로봇이 초기화되었습니다")
                print("✅ Doosan机器人已初始化")
            except Exception as e:
                print(f"❌ Failed to initialize robot: {e}")
                print(f"❌ 로봇 초기화 실패: {e}")
                print(f"❌ 机器人初始化失败: {e}")
                print("🔄 Using simulator mode")
                print("🔄 시뮬레이터 모드 사용")
                print("🔄 使用仿真模式")
                self.robot = RobotSimulator()
        else:
            self.robot = RobotSimulator()
            print("🔄 Running in simulation mode")
            print("🔄 시뮬레이션 모드에서 실행 중")
            print("🔄 仿真模式运行中")

    def start_server(self):
        """启动TCP服务器 / TCP 서버 시작 / Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"🚀 DART Studio Server started on {self.host}:{self.port}")
            print(f"🚀 DART Studio 서버가 {self.host}:{self.port}에서 시작되었습니다")
            print(f"🚀 DART Studio服务器已在{self.host}:{self.port}启动")
            print(f"🔑 Token: {self.token}")
            print(f"🔑 토큰: {self.token}")
            print(f"🔑 令牌: {self.token}")
            print("⏳ Waiting for connections...")
            print("⏳ 연결을 기다리는 중...")
            print("⏳ 等待连接...")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"🔌 New connection from {address}")
                    print(f"🔌 {address}에서 새로운 연결")
                    print(f"🔌 来自{address}的新连接")

                    # Handle client in separate thread / 별도 스레드에서 클라이언트 처리 / 在单独线程中处理客户端
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        print(f"❌ Socket error: {e}")
                        print(f"❌ 소켓 오류: {e}")
                        print(f"❌ 套接字错误: {e}")

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            print(f"❌ 서버 시작 실패: {e}")
            print(f"❌ 服务器启动失败: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """停止服务器 / 서버 정지 / Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 Server stopped")
        print("🛑 서버 정지됨")
        print("🛑 服务器已停止")

    def handle_client(self, client_socket, address):
        """处理单个客户端连接 / 개별 클라이언트 연결 처리 / Handle individual client connection"""
        authenticated = False

        try:
            while self.running:
                # Receive data / 데이터 수신 / 接收数据
                data = client_socket.recv(4096)
                if not data:
                    break

                try:
                    # Parse JSON message / JSON 메시지 파싱 / 解析JSON消息
                    message = json.loads(data.decode('utf-8').strip())
                    print(f"📨 Received from {address}: {message}")
                    print(f"📨 {address}에서 수신: {message}")
                    print(f"📨 从{address}接收: {message}")

                    # Process message / 메시지 처리 / 处理消息
                    response = self.process_message(message, authenticated)

                    # Update authentication status / 인증 상태 업데이트 / 更新认证状态
                    if message.get('type') == 'auth' and response.get('status') == 'ok':
                        authenticated = True

                    # Send response / 응답 전송 / 发送响应
                    response_data = json.dumps(response) + "\n"
                    client_socket.send(response_data.encode('utf-8'))
                    print(f"📤 Sent to {address}: {response}")
                    print(f"📤 {address}에 전송: {response}")
                    print(f"📤 发送到{address}: {response}")

                except json.JSONDecodeError as e:
                    error_response = {"status": "error", "message": f"Invalid JSON / 잘못된 JSON / JSON格式错误: {e}"}
                    client_socket.send((json.dumps(error_response) + "\n").encode('utf-8'))
                except Exception as e:
                    error_response = {"status": "error", "message": f"Processing error / 처리 오류 / 处理错误: {e}"}
                    client_socket.send((json.dumps(error_response) + "\n").encode('utf-8'))

        except Exception as e:
            print(f"❌ Client {address} error: {e}")
            print(f"❌ 클라이언트 {address} 오류: {e}")
            print(f"❌ 客户端{address}错误: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Client {address} disconnected")
            print(f"🔌 클라이언트 {address} 연결 해제")
            print(f"🔌 客户端{address}已断开连接")

    def process_message(self, message: Dict[str, Any], authenticated: bool) -> Dict[str, Any]:
        """处理传入消息并返回响应 / 수신된 메시지 처리 및 응답 반환 / Process incoming message and return response"""

        msg_type = message.get('type')
        token = message.get('token')

        # Token validation / 토큰 검증 / 令牌验证
        if token != self.token:
            return {"status": "error", "message": "Invalid token / 잘못된 토큰 / 无效令牌"}

        # Handle authentication / 인증 처리 / 处理认证
        if msg_type == 'auth':
            return {"status": "ok", "message": "Authentication successful / 인증 성공 / 认证成功"}

        # Require authentication for other commands / 다른 명령에는 인증 필요 / 其他命令需要认证
        if not authenticated and msg_type != 'ping':
            return {"status": "error", "message": "Authentication required / 인증 필요 / 需要认证"}

        # Handle different message types / 다양한 메시지 유형 처리 / 处理不同消息类型
        if msg_type == 'ping':
            return {"status": "ok", "pong": True}

        elif msg_type == 'call':
            return self.handle_function_call(message)

        elif msg_type == 'sequence':
            return self.handle_sequence(message)

        else:
            return {"status": "error", "message": f"Unknown message type / 알 수 없는 메시지 유형 / 未知消息类型: {msg_type}"}

    def handle_function_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理函数调用请求 / 함수 호출 요청 처리 / Handle function call requests"""
        function = message.get('function')
        args = message.get('args', {})

        print(f"🤖 Executing function: {function} with args: {args}")
        print(f"🤖 함수 실행: {function} 인수: {args}")
        print(f"🤖 执行函数: {function}，参数: {args}")

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
                return {"status": "error", "message": f"Unknown function / 알 수 없는 함수 / 未知函数: {function}"}

        except Exception as e:
            return {"status": "error", "message": f"Function execution error / 함수 실행 오류 / 函数执行错误: {e}"}

    def handle_sequence(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理命令序列 / 명령 시퀀스 처리 / Handle sequence of commands"""
        commands = message.get('commands', [])
        results = []

        for i, command in enumerate(commands):
            print(f"🔄 Executing command {i + 1}/{len(commands)}: {command}")
            print(f"🔄 명령 실행 중 {i + 1}/{len(commands)}: {command}")
            print(f"🔄 执行命令 {i + 1}/{len(commands)}: {command}")

            # Process each command as a function call / 각 명령을 함수 호출로 처리 / 将每个命令作为函数调用处理
            result = self.handle_function_call(command)
            results.append(result)

            # Stop on error / 오류 시 중지 / 出错时停止
            if result.get('status') != 'ok':
                break

        return {
            "status": "ok",
            "total_commands": len(commands),
            "executed_commands": len(results),
            "results": results
        }

    # Robot function implementations / 로봇 함수 구현 / 机器人函数实现
    def execute_move_j(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行关节移动 / 관절 이동 실행 / Execute joint movement"""
        positions = args.get('positions', [])
        speed = args.get('speed', 0.2)

        if len(positions) != 6:
            return {"status": "error", "message": "MoveJ requires 6 joint positions / MoveJ는 6개의 관절 위치가 필요합니다 / MoveJ需要6个关节位置"}

        try:
            if DART_STUDIO_AVAILABLE and hasattr(self.robot, 'movej'):
                # Real robot implementation / 실제 로봇 구현 / 实际机器人实现
                success = self.robot.movej(positions, speed)
            else:
                # Simulator implementation / 시뮬레이터 구현 / 仿真器实现
                success = self.robot.movej(positions, speed)

            if success:
                return {
                    "status": "ok",
                    "message": f"MoveJ completed / MoveJ 완료 / MoveJ完成",
                    "positions": positions,
                    "speed": speed
                }
            else:
                return {"status": "error", "message": "MoveJ failed / MoveJ 실패 / MoveJ失败"}

        except Exception as e:
            return {"status": "error", "message": f"MoveJ error / MoveJ 오류 / MoveJ错误: {e}"}

    def execute_move_l(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行直线移动 / 직선 이동 실행 / Execute linear movement"""
        positions = args.get('positions', [])
        speed = args.get('speed', 0.2)

        if len(positions) != 6:
            return {"status": "error", "message": "MoveL requires 6 pose values [x,y,z,rx,ry,rz] / MoveL는 6개의 자세 값 [x,y,z,rx,ry,rz]가 필요합니다 / MoveL需要6个位姿值[x,y,z,rx,ry,rz]"}

        try:
            if DART_STUDIO_AVAILABLE and hasattr(self.robot, 'movel'):
                # Real robot implementation / 실제 로봇 구현 / 实际机器人实现
                success = self.robot.movel(positions, speed)
            else:
                # Simulator implementation / 시뮬레이터 구현 / 仿真器实现
                success = self.robot.movel(positions, speed)

            if success:
                return {
                    "status": "ok",
                    "message": f"MoveL completed / MoveL 완료 / MoveL完成",
                    "positions": positions,
                    "speed": speed
                }
            else:
                return {"status": "error", "message": "MoveL failed / MoveL 실패 / MoveL失败"}

        except Exception as e:
            return {"status": "error", "message": f"MoveL error / MoveL 오류 / MoveL错误: {e}"}

    def execute_set_do(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """设置数字输出 / 디지털 출력 설정 / Set digital output"""
        pin = args.get('pin')
        value = args.get('value')

        if pin is None or value is None:
            return {"status": "error", "message": "SetDO requires pin and value / SetDO는 핀과 값이 필요합니다 / SetDO需要引脚和值"}

        try:
            success = self.robot.set_digital_output(pin, value)
            if success:
                return {
                    "status": "ok",
                    "message": f"DO{pin} set to {value} / DO{pin}이 {value}로 설정됨 / DO{pin}设置为{value}",
                    "pin": pin,
                    "value": value
                }
            else:
                return {"status": "error", "message": f"Failed to set DO{pin} / DO{pin} 설정 실패 / 设置DO{pin}失败"}

        except Exception as e:
            return {"status": "error", "message": f"SetDO error / SetDO 오류 / SetDO错误: {e}"}

    def execute_get_di(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取数字输入 / 디지털 입력 가져오기 / Get digital input"""
        pin = args.get('pin')

        if pin is None:
            return {"status": "error", "message": "GetDI requires pin / GetDI는 핀이 필요합니다 / GetDI需要引脚"}

        try:
            value = self.robot.get_digital_input(pin)
            return {
                "status": "ok",
                "pin": pin,
                "value": value
            }
        except Exception as e:
            return {"status": "error", "message": f"GetDI error / GetDI 오류 / GetDI错误: {e}"}

    def execute_wait_ms(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """等待指定毫秒 / 지정된 밀리초 대기 / Wait for specified milliseconds"""
        ms = args.get('ms', 0)

        try:
            time.sleep(ms / 1000.0)
            return {
                "status": "ok",
                "message": f"Waited {ms}ms / {ms}ms 대기함 / 等待了{ms}毫秒"
            }
        except Exception as e:
            return {"status": "error", "message": f"Wait error / 대기 오류 / 等待错误: {e}"}

    def execute_get_current_pose(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取当前机器人位姿 / 현재 로봇 자세 가져오기 / Get current robot pose"""
        try:
            if DART_STUDIO_AVAILABLE and hasattr(self.robot, 'get_current_pose'):
                pose = self.robot.get_current_pose()
            else:
                pose = self.robot.current_pose

            return {
                "status": "ok",
                "pose": pose
            }
        except Exception as e:
            return {"status": "error", "message": f"GetCurrentPose error / GetCurrentPose 오류 / GetCurrentPose错误: {e}"}

    def execute_get_joint_angles(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取当前关节角度 / 현재 관절 각도 가져오기 / Get current joint angles"""
        try:
            if DART_STUDIO_AVAILABLE and hasattr(self.robot, 'get_current_joints'):
                joints = self.robot.get_current_joints()
            else:
                joints = self.robot.current_joints

            return {
                "status": "ok",
                "joints": joints
            }
        except Exception as e:
            return {"status": "error", "message": f"GetJointAngles error / GetJointAngles 오류 / GetJointAngles错误: {e}"}

    def execute_emergency_stop(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行紧急停止 / 비상 정지 실행 / Execute emergency stop"""
        try:
            success = self.robot.emergency_stop()
            if success:
                return {
                    "status": "ok",
                    "message": "Emergency stop executed / 비상 정지 실행됨 / 紧急停止已执行"
                }
            else:
                return {"status": "error", "message": "Emergency stop failed / 비상 정지 실패 / 紧急停止失败"}
        except Exception as e:
            return {"status": "error", "message": f"Emergency stop error / 비상 정지 오류 / 紧急停止错误: {e}"}

    def execute_reset_robot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """复位机器人 / 로봇 리셋 / Reset robot"""
        try:
            success = self.robot.reset_robot()
            if success:
                return {
                    "status": "ok",
                    "message": "Robot reset completed / 로봇 리셋 완료 / 机器人复位完成"
                }
            else:
                return {"status": "error", "message": "Robot reset failed / 로봇 리셋 실패 / 机器人复位失败"}
        except Exception as e:
            return {"status": "error", "message": f"Reset error / 리셋 오류 / 复位错误: {e}"}

    def execute_get_robot_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取机器人状态 / 로봇 상태 가져오기 / Get robot state"""
        try:
            if DART_STUDIO_AVAILABLE and hasattr(self.robot, 'get_robot_state'):
                state = self.robot.get_robot_state()
            else:
                state = {
                    "robot_state": self.robot.robot_state,
                    "is_moving": False,
                    "is_ready": True
                }

            return {
                "status": "ok",
                "robot_state": state
            }
        except Exception as e:
            return {"status": "error", "message": f"GetRobotState error / GetRobotState 오류 / GetRobotState错误: {e}"}


def main():
    """主函数 / 메인 함수 / Main function"""
    print("🤖 DART Studio Server for Doosan Robot")
    print("🤖 Doosan 로봇용 DART Studio 서버")
    print("🤖 Doosan机器人DART Studio服务器")
    print("=" * 50)

    # Configuration / 구성 / 配置
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    token = DEFAULT_TOKEN

    # Create and start server / 서버 생성 및 시작 / 创建并启动服务器
    server = DartStudioServer(host, port, token)

    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nℹ️  Server interrupted by user")
        print("\nℹ️  사용자에 의해 서버가 중단됨")
        print("\nℹ️  服务器被用户中断")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print(f"❌ 서버 오류: {e}")
        print(f"❌ 服务器错误: {e}")
    finally:
        server.stop_server()


if __name__ == "__main__":
    main()

"""
DART Studio Integration Notes / DART Studio 통합 주의사항 / DART Studio集成注意事项:

1. In real DART Studio environment, replace the robot simulator with actual Doosan robot API calls
   실제 DART Studio 환경에서는 로봇 시뮬레이터를 실제 Doosan 로봇 API 호출로 교체하세요
   在真实的DART Studio环境中，用实际的Doosan机器人API调用替换机器人仿真器

2. Import the correct DART Studio modules (e.g., dsr_robot, dsr_msgs)
   올바른 DART Studio 모듈을 가져오세요 (예: dsr_robot, dsr_msgs)
   导入正确的DART Studio模块（例如：dsr_robot, dsr_msgs）

3. Configure robot initialization parameters according to your robot model
   로봇 모델에 따라 로봇 초기화 매개변수를 구성하세요
   根据您的机器人型号配置机器人初始化参数

4. Adjust safety limits and workspace boundaries
   안전 한계와 작업 공간 경계를 조정하세요
   调整安全限制和工作空间边界

5. Add robot-specific error handling
   로봇별 오류 처리를 추가하세요
   添加特定于机器人的错误处理

Example real robot initialization (to be adapted) / 실제 로봇 초기화 예제 (적용 필요) / 实际机器人初始化示例（需要调整）:
```python
from dsr_robot import Robot
from dsr_msgs.msg import RobotState, RobotError

robot = Robot()
robot.set_robot_mode(RobotMode.MANUAL)  # or appropriate mode / 또는 적절한 모드 / 或适当模式
robot.set_robot_system(RobotSystem.REAL)
```

Usage / 사용법 / 使用方法:
1. Copy this script to DART Studio environment / 이 스크립트를 DART Studio 환경으로 복사 / 将此脚本复制到DART Studio环境
2. Modify robot initialization code for your specific setup / 특정 설정에 맞게 로봇 초기화 코드 수정 / 根据您的特定设置修改机器人初始化代码
3. Run the script in DART Studio / DART Studio에서 스크립트 실행 / 在DART Studio中运行脚本
4. The server will listen on port 9000 for Python client connections / 서버는 Python 클라이언트 연결을 위해 포트 9000에서 대기 / 服务器将在端口9000监听Python客户端连接
5. Test with your Python client code / Python 클라이언트 코드로 테스트 / 使用您的Python客户端代码进行测试
"""