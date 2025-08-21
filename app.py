"""
机械臂通信框架主程序 / 로봇 암 통신 프레임워크 메인 프로그램 / Robotic Arm Communication Framework Main Program
========================================================================================================

作用 / 역할 / Purpose:
----------------------
这是整个机械臂通信系统的主入口程序，负责：
1. 初始化与DART Studio的通信连接
2. 提供用户交互界面，测试各种机械臂操作功能
3. 集成基础控制功能和煎面包逻辑占位符
4. 处理异常情况和紧急停止

이 프로그램은 전체 로봇 암 통신 시스템의 메인 엔트리 포인트로서 다음 역할을 담당합니다:
1. DART Studio와의 통신 연결 초기화
2. 다양한 로봇 암 작업 기능을 테스트하기 위한 사용자 인터페이스 제공
3. 기본 제어 기능과 빵 굽기 로직 플레이스홀더 통합
4. 예외 상황 및 비상 정지 처리

This is the main entry point for the entire robotic arm communication system, responsible for:
1. Initializing communication connection with DART Studio
2. Providing user interface to test various robotic arm operation functions
3. Integrating basic control functions and bread toasting logic placeholders
4. Handling exceptions and emergency stops

使用方式 / 사용 방법 / Usage:
----------------------
1. 基本运行 / 기본 실행 / Basic execution:
   ```bash
   python app.py
   ```

2. 通信测试模式 / 통신 테스트 모드 / Communication test mode:
   ```bash
   python app.py --test
   ```

3. 配置连接参数 / 연결 매개변수 구성 / Configure connection parameters:
   - 修改 DART_HOST, DART_PORT, DART_TOKEN 变量
   - DART_HOST, DART_PORT, DART_TOKEN 변수 수정
   - Modify DART_HOST, DART_PORT, DART_TOKEN variables

系统架构 / 시스템 아키텍처 / System Architecture:
----------------------
app.py (用户界면/사용자 인터페이스/User Interface)
    ↓
arm_logic.py (逻辑层/로직 계층/Logic Layer)
    ↓
dart_link.py (通信层/통신 계층/Communication Layer)
    ↓
DART Studio (机器人控制/로봇 제어/Robot Control)

主要功能 / 주요 기능 / Main Functions:
----------------------
- main(): 주프로그램 루프 / 메인 프로그램 루프 / Main program loop
- test_communication(): 基础通信测试 / 기본 통신 테스트 / Basic communication test

菜单选项 / 메뉴 옵션 / Menu Options:
----------------------
1. 回到初始位置 / 홈 위치로 이동 / Return to home position
2. 测试关节移动 / 관절 이동 테스트 / Test joint movement
3. 测试直线移动 / 직선 이동 테스트 / Test linear movement
4. 测试夹爪控制 / 그리퍼 제어 테스트 / Test gripper control
5. 获取机器人状态 / 로봇 상태 가져오기 / Get robot status
6. 紧急停止 / 비상 정지 / Emergency stop
7-10. 煎面包逻辑占位符 / 빵 굽기 로직 플레이스홀더 / Bread toasting logic placeholders

错误处理 / 오류 처리 / Error Handling:
----------------------
- DartLinkException: DART通信错误 / DART 통신 오류 / DART communication errors
- KeyboardInterrupt: 用户中断处理 / 사용자 중단 처리 / User interruption handling
- Exception: 通用异常处理 / 일반 예외 처리 / General exception handling
"""

import sys
import logging
from dart_link import DartLink, DartLinkException
from arm_logic import ArmLogic

# 配置简单日志 / 간단한 로깅 설정 / Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主程序 - 专注于通信框架测试 / 메인 프로그램 - 통신 프레임워크 테스트에 중점 / Main program - focused on communication framework testing"""
    # 连接配置 / 연결 구성 / Connection configuration
    DART_HOST = "192.168.10.10"
    DART_PORT = 9000
    DART_TOKEN = "TEST_TOKEN_123"  # 请更改为实际token / 실제 토큰으로 변경하세요 / Please change to actual token

    try:
        logger.info("初始化机械臂连接... / 로봇 암 연결 초기화 중... / Initializing robotic arm connection...")
        link = DartLink(host=DART_HOST, port=DART_PORT, token=DART_TOKEN)

        # 连通性检查 / 연결성 확인 / Connectivity check
        logger.info("检查连接状态... / 연결 상태 확인 중... / Checking connection status...")
        if not link.ping():
            logger.error("无法连接到DART Studio，请检查网络连接和DART Studio状态 / DART Studio에 연결할 수 없습니다. 네트워크 연결과 DART Studio 상태를 확인하세요 / Unable to connect to DART Studio, please check network connection and DART Studio status")
            return 1

        logger.info("连接成功！/ 연결 성공! / Connection successful!")

        # 创建机械臂逻辑控制器 / 로봇 암 로직 컨트롤러 생성 / Create robotic arm logic controller
        logic = ArmLogic(link)

        # 用户交互菜单 / 사용자 상호작용 메뉴 / User interaction menu
        while True:
            print("\n=== 机械臂通信框架测试系统 / 로봇 암 통신 프레임워크 테스트 시스템 / Robotic Arm Communication Framework Test System ===")
            print("基础控制测试 / 기본 제어 테스트 / Basic Control Tests:")
            print("1. 回到初始位置 (Home) / 홈 위치로 이동 (Home) / Return to Home Position")
            print("2. 测试关节移动 (MoveJ) / 관절 이동 테스트 (MoveJ) / Test Joint Movement (MoveJ)")
            print("3. 测试直线移动 (MoveL) / 직선 이동 테스트 (MoveL) / Test Linear Movement (MoveL)")
            print("4. 测试夹爪控制 / 그리퍼 제어 테스트 / Test Gripper Control")
            print("5. 获取机器人状态 / 로봇 상태 가져오기 / Get Robot Status")
            print("6. 紧急停止 / 비상 정지 / Emergency Stop")
            print("")
            print("煎面包逻辑占位符 / 빵 굽기 로직 플레이스홀더 / Bread Toasting Logic Placeholders:")
            print("7. 测试抓取面包 (占位符) / 빵 잡기 테스트 (플레이스홀더) / Test Bread Picking (Placeholder)")
            print("8. 测试放置面包 (占位符) / 빵 놓기 테스트 (플레이스홀더) / Test Bread Placement (Placeholder)")
            print("9. 测试翻转面包 (占位符) / 빵 뒤집기 테스트 (플레이스홀더) / Test Bread Flipping (Placeholder)")
            print("10. 测试完整流程 (占位符) / 전체 과정 테스트 (플레이스홀더) / Test Complete Process (Placeholder)")
            print("")
            print("0. 退出 / 종료 / Exit")

            try:
                choice = input("\n请选择操作 (0-10) / 작업을 선택하세요 (0-10) / Please select operation (0-10): ").strip()

                if choice == "0":
                    logger.info("程序退出 / 프로그램 종료 / Program exit")
                    break

                elif choice == "1":
                    print("执行回零... / 홈 위치로 이동 중... / Executing home position...")
                    result = logic.home()
                    print(f"结果 / 결과 / Result: {result}")

                elif choice == "2":
                    print("测试关节移动 - 请输入6个关节角度，用逗号分隔 / 관절 이동 테스트 - 6개의 관절 각도를 쉼표로 구분하여 입력하세요 / Test joint movement - Please enter 6 joint angles separated by commas")
                    positions_input = input("关节角度 (默认: 10,0,0,0,0,0) / 관절 각도 (기본값: 10,0,0,0,0,0) / Joint angles (default: 10,0,0,0,0,0): ").strip()
                    if not positions_input:
                        positions = [10, 0, 0, 0, 0, 0]
                    else:
                        try:
                            positions = [float(x.strip()) for x in positions_input.split(',')]
                            if len(positions) != 6:
                                print("需要输入6个角度值 / 6개의 각도 값이 필요합니다 / Need to input 6 angle values")
                                continue
                        except ValueError:
                            print("输入格式错误 / 입력 형식 오류 / Input format error")
                            continue

                    speed = input("速度 (0.1-1.0, 默认0.2) / 속도 (0.1-1.0, 기본값 0.2) / Speed (0.1-1.0, default 0.2): ").strip()
                    speed = float(speed) if speed and speed.replace('.', '').isdigit() else 0.2

                    result = logic.test_move_j(positions, speed)
                    print(f"MoveJ结果 / MoveJ 결과 / MoveJ Result: {result}")

                elif choice == "3":
                    print("测试直线移动 - 请输入6个位姿参数 [x,y,z,rx,ry,rz]，用逗号分隔 / 직선 이동 테스트 - 6개의 자세 매개변수 [x,y,z,rx,ry,rz]를 쉼표로 구분하여 입력하세요 / Test linear movement - Please enter 6 pose parameters [x,y,z,rx,ry,rz] separated by commas")
                    positions_input = input("位姿参数 (默认: 400,0,300,0,0,0) / 자세 매개변수 (기본값: 400,0,300,0,0,0) / Pose parameters (default: 400,0,300,0,0,0): ").strip()
                    if not positions_input:
                        positions = [400, 0, 300, 0, 0, 0]
                    else:
                        try:
                            positions = [float(x.strip()) for x in positions_input.split(',')]
                            if len(positions) != 6:
                                print("需要输入6个位姿参数 / 6개의 자세 매개변수가 필요합니다 / Need to input 6 pose parameters")
                                continue
                        except ValueError:
                            print("输入格式错误 / 입력 형식 오류 / Input format error")
                            continue

                    speed = input("速度 (0.1-1.0, 默认0.2) / 속도 (0.1-1.0, 기본값 0.2) / Speed (0.1-1.0, default 0.2): ").strip()
                    speed = float(speed) if speed and speed.replace('.', '').isdigit() else 0.2

                    result = logic.test_move_l(positions, speed)
                    print(f"MoveL结果 / MoveL 결과 / MoveL Result: {result}")

                elif choice == "4":
                    action = input("夹爪动作 - 关闭(c)/打开(o) / 그리퍼 동작 - 닫기(c)/열기(o) / Gripper action - close(c)/open(o): ").strip().lower()
                    if action == "c":
                        result = logic.test_gripper(True)
                    elif action == "o":
                        result = logic.test_gripper(False)
                    else:
                        print("无效输入 / 잘못된 입력 / Invalid input")
                        continue
                    print(f"夹爪控制结果 / 그리퍼 제어 결과 / Gripper control result: {result}")

                elif choice == "5":
                    print("获取机器人状态... / 로봇 상태 가져오기 중... / Getting robot status...")
                    result = logic.get_current_status()
                    print(f"状态信息 / 상태 정보 / Status information: {result}")

                elif choice == "6":
                    print("执行紧急停止... / 비상 정지 실행 중... / Executing emergency stop...")
                    result = logic.emergency_stop()
                    print(f"紧急停止结果 / 비상 정지 결과 / Emergency stop result: {result}")

                # 煎面包占位符功能 / 빵 굽기 플레이스홀더 기능 / Bread toasting placeholder functions
                elif choice == "7":
                    print("测试抓取面包占位符... / 빵 잡기 플레이스홀더 테스트 중... / Testing bread picking placeholder...")
                    result = logic.pick_bread()
                    print(f"抓取面包占位符结果 / 빵 잡기 플레이스홀더 결과 / Bread picking placeholder result: {result}")

                elif choice == "8":
                    print("测试放置面包占位符... / 빵 놓기 플레이스홀더 테스트 중... / Testing bread placement placeholder...")
                    result = logic.place_on_pan()
                    print(f"放置面包占位符结果 / 빵 놓기 플레이스홀더 결과 / Bread placement placeholder result: {result}")

                elif choice == "9":
                    print("测试翻转面包占位符... / 빵 뒤집기 플레이스홀더 테스트 중... / Testing bread flipping placeholder...")
                    result = logic.flip_bread()
                    print(f"翻转面包占位符结果 / 빵 뒤집기 플레이스홀더 결과 / Bread flipping placeholder result: {result}")

                elif choice == "10":
                    print("测试完整煎面包流程占位符... / 전체 빵 굽기 과정 플레이스홀더 테스트 중... / Testing complete bread toasting process placeholder...")
                    result = logic.toast_cycle()
                    print(f"完整流程占位符结果 / 전체 과정 플레이스홀더 결과 / Complete process placeholder result: {result}")

                else:
                    print("无效选择，请重新输入 / 잘못된 선택, 다시 입력하세요 / Invalid selection, please re-enter")

            except KeyboardInterrupt:
                logger.info("用户中断，执行紧急停止... / 사용자 중단, 비상 정지 실행 중... / User interruption, executing emergency stop...")
                logic.emergency_stop()
                break
            except Exception as e:
                logger.error(f"操作异常 / 작업 예외 / Operation exception: {e}")
                print(f"操作失败 / 작업 실패 / Operation failed: {e}")

    except DartLinkException as e:
        logger.error(f"DART通信错误 / DART 통신 오류 / DART communication error: {e}")
        return 1
    except Exception as e:
        logger.error(f"程序异常 / 프로그램 예외 / Program exception: {e}")
        return 1

    return 0


def test_communication():
    """基础通信测试 / 기본 통신 테스트 / Basic communication test"""
    print("开始通信框架测试... / 통신 프레임워크 테스트 시작... / Starting communication framework test...")

    link = DartLink()

    # 测试连接 / 연결 테스트 / Test connection
    if not link.ping():
        print("❌ 连接失败，请检查DART Studio是否启动 / 연결 실패, DART Studio가 시작되었는지 확인하세요 / Connection failed, please check if DART Studio is running")
        return

    print("✅ 连接成功 / 연결 성공 / Connection successful")

    # 测试基础指令 / 기본 명령 테스트 / Test basic commands
    tests = [
        ("Ping测试 / Ping 테스트 / Ping test", lambda: link.ping()),
        ("获取位姿 / 현재 자세 가져오기 / Get current pose", lambda: link.get_current_pose()),
        ("获取关节角度 / 현재 관절 각도 가져오기 / Get joint angles", lambda: link.get_joint_angles()),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            print(f"✅ {test_name}: {result}")
        except Exception as e:
            print(f"❌ {test_name}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="机械臂通信框架测试系统 / 로봇 암 통신 프레임워크 테스트 시스템 / Robotic Arm Communication Framework Test System")
    parser.add_argument("--test", action="store_true", help="运行通信测试 / 통신 테스트 실행 / Run communication test")

    args = parser.parse_args()

    if args.test:
        test_communication()
    else:
        sys.exit(main())