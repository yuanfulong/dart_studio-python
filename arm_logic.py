"""
ArmLogic 模块 / ArmLogic 모듈 / ArmLogic Module
====================================================

作用 / 역할 / Purpose:
----------------------
这个文件在 DartLink 通信层的基础上，封装了更高层次的机械臂操作逻辑。
它通过调用 DartLink 的底层函数，实现更安全、简化的机器人控制，并提供了“煎面包”相关的占位符逻辑。

이 파일은 DartLink 통신 계층을 기반으로, 상위 수준의 로봇 제어 로직을 캡슐화합니다.
DartLink의 저수준 함수를 호출하여 더 안전하고 단순한 제어를 구현하며, "빵 굽기" 관련 플레이스홀더 로직도 제공합니다.

This file builds on the DartLink communication layer, encapsulating higher-level robot control logic.
It invokes DartLink’s low-level functions to provide safer, simplified operations, and includes placeholder logic for "bread toasting."

类 / 클래스 / Class:
----------------------
- `ArmLogic`: 逻辑控制层，依赖于 `DartLink` 对象。
  - 提供基础动作封装（回零、安全位置、关节/直线移动、夹爪测试、状态查询、急停、复位等）。
  - 提供高级功能（路径点序列执行、煎面包流程占位符等）。

- `ArmLogic` 클래스는 `DartLink` 객체에 의존하는 제어 계층입니다.
  - 기본 동작 (홈, 안전 위치, 관절/직선 이동, 그리퍼 테스트, 상태 조회, 비상 정지, 초기화 등)을 제공합니다.
  - 고급 기능 (경로점 시퀀스 실행, 빵 굽기 플레이스홀더 등)을 제공합니다.

- `ArmLogic` class is a control layer built on a `DartLink` instance.
  - Provides basic operations (home, safe position, joint/linear moves, gripper test, status queries, emergency stop, reset, etc.).
  - Provides advanced features (waypoint sequence execution, bread toasting placeholder logic).

使用方式 / 사용 방법 / Usage:
----------------------
1. 创建 DartLink 并连接 / DartLink 객체 생성 및 연결 / Create DartLink and connect:
   ```python
   from dart_link import DartLink
   from arm_logic import ArmLogic

   link = DartLink(host="192.168.10.10", port=9000, token="YOUR_TOKEN")
   link.connect()
   logic = ArmLogic(link)
   ```

2. 调用 ArmLogic 的函数执行动作 / ArmLogic 함수 호출로 동작 실행 / Call ArmLogic functions to perform actions:
   ```python
   logic.home()               # 回到初始位置 / 홈 위치로 이동 / Move to home position
   logic.test_move_j([...])   # 关节运动测试 / 관절 이동 테스트 / Test joint movement
   logic.toast_cycle()        # 煎面包流程（占位符）/ 빵 굽기 절차 (플레이스홀더) / Bread toasting cycle (placeholder)
   ```

数据格式 / 데이터 형식 / Data format:
----------------------
ArmLogic 所有函数返回字典，包含至少以下键：
- `status`: "ok" 或 "error" / "ok" 또는 "error" / "ok" or "error"
- `function` 或 `message`: 指明执行的动作 / 실행된 동작 설명 / description of the executed action
- 可能包含 `data`, `error`, `todo` 等字段 / `data`, `error`, `todo` 등의 필드 포함 가능 / may include `data`, `error`, `todo`, etc.

函数说明 / 함수 설명 / Function descriptions:
----------------------
- `home()`                  回到初始位置 / 홈 위치 / Move to home position
- `move_to_safe_position()` 移动到安全观察位置 / 안전 위치 이동 / Move to safe observation position
- `test_move_j()`           测试关节移动 / 관절 이동 테스트 / Test joint movement
- `test_move_l()`           测试直线移动 / 직선 이동 테스트 / Test linear movement
- `test_gripper()`          测试夹爪开合 / 그리퍼 동작 테스트 / Test gripper open/close
- `get_current_status()`    获取当前状态 / 현재 상태 가져오기 / Get current status
- `emergency_stop()`        紧急停止 / 비상 정지 / Emergency stop
- `reset_robot()`           复位机器人 / 로봇 초기화 / Reset robot
- `move_sequence()`         执行一系列路径点 / 경로점 시퀀스 실행 / Execute series of waypoints
- `pick_bread()`            占位符：抓取面包 / 플레이스홀더: 빵 잡기 / Placeholder: pick bread
- `place_on_pan()`          占位符：放置面包 / 플레이스홀더: 빵 놓기 / Placeholder: place bread on pan
- `flip_bread()`            占位符：翻转面包 / 플레이스홀더: 빵 뒤집기 / Placeholder: flip bread
- `control_heating()`       占位符：控制加热 / 플레이스홀더: 가열 제어 / Placeholder: control heating
- `toast_cycle()`           占位符：煎面包完整流程 / 플레이스홀더: 빵 굽기 전체 절차 / Placeholder: complete bread toasting cycle
"""

from typing import List, Dict, Any, Optional
import logging
import time
from dart_link import DartLink, DartLinkException

logger = logging.getLogger(__name__)


class ArmLogic:
    def __init__(self, link: DartLink):
        self.link = link
        # 安全位置定义
        self.home_position = [0, 0, 0, 0, 0, 0]  # 机器人初始位置
        self.safe_position = [0, -20, 40, 0, -20, 0]  # 安全观察位置

        # 夹爪配置
        self.gripper_pin = 1  # 夹爪控制引脚
        self.gripper_close_value = True
        self.gripper_open_value = False

    def _execute_safely(self, func_name: str, func) -> Dict[str, Any]:
        """安全执行函数包装器"""
        try:
            logger.info(f"执行: {func_name}")
            result = func()

            # 检查结果
            if isinstance(result, dict):
                if result.get("status") == "ok":
                    logger.info(f"{func_name} 执行成功")
                    return {"status": "ok", "function": func_name, "data": result}
                else:
                    error_msg = result.get("message", "未知错误")
                    logger.error(f"{func_name} 执行失败: {error_msg}")
                    return {"status": "error", "function": func_name, "error": error_msg}
            else:
                logger.info(f"{func_name} 执行成功")
                return {"status": "ok", "function": func_name, "data": result}

        except Exception as e:
            logger.error(f"{func_name} 异常: {e}")
            return {"status": "error", "function": func_name, "error": str(e)}

    def _check_connection(self) -> bool:
        """检查连接状态"""
        try:
            return self.link.ping()
        except:
            return False

    # ============ 基础控制函数 ============
    def home(self) -> Dict[str, Any]:
        """回到初始位置"""

        def _home():
            return self.link.move_j(self.home_position, speed=0.2)

        return self._execute_safely("home", _home)

    def move_to_safe_position(self) -> Dict[str, Any]:
        """移动到安全观察位置"""

        def _safe():
            return self.link.move_j(self.safe_position, speed=0.2)

        return self._execute_safely("move_to_safe_position", _safe)

    def test_move_j(self, positions: List[float], speed: float = 0.2) -> Dict[str, Any]:
        """测试关节移动"""

        def _test():
            # 参数验证
            if len(positions) != 6:
                raise ValueError("需要6个关节角度")
            if not (0.01 <= speed <= 1.0):
                raise ValueError("速度必须在0.01-1.0之间")

            # 安全检查 - 限制关节角度范围
            for i, pos in enumerate(positions):
                if abs(pos) > 180:  # 简单的角度范围检查
                    logger.warning(f"关节{i + 1}角度{pos}可能超出安全范围")

            return self.link.move_j(positions, speed)

        return self._execute_safely("test_move_j", _test)

    def test_move_l(self, positions: List[float], speed: float = 0.2) -> Dict[str, Any]:
        """测试直线移动"""

        def _test():
            if len(positions) != 6:
                raise ValueError("需要6个位姿参数[x,y,z,rx,ry,rz]")
            if not (0.01 <= speed <= 1.0):
                raise ValueError("速度必须在0.01-1.0之间")

            # 基本工作空间检查（根据你的机器人调整）
            x, y, z = positions[:3]
            if not (200 <= ((x ** 2 + y ** 2 + z ** 2) ** 0.5) <= 1000):
                logger.warning("目标位置可能超出工作空间")

            return self.link.move_l(positions, speed)

        return self._execute_safely("test_move_l", _test)

    def test_gripper(self, close: bool = True) -> Dict[str, Any]:
        """测试夹爪"""

        def _test():
            value = self.gripper_close_value if close else self.gripper_open_value
            return self.link.set_digital_output(self.gripper_pin, value)

        action = "关闭" if close else "打开"
        return self._execute_safely(f"test_gripper_{action}", _test)

    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        try:
            if not self._check_connection():
                return {"status": "error", "error": "连接已断开"}

            # 获取多种状态信息
            pose_result = self.link.get_current_pose()
            joint_result = self.link.get_joint_angles()
            robot_state = self.link.get_robot_state()

            return {
                "status": "ok",
                "timestamp": time.time(),
                "current_pose": pose_result,
                "current_joints": joint_result,
                "robot_state": robot_state,
                "connection": "ok"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def emergency_stop(self) -> Dict[str, Any]:
        """紧急停止"""

        def _stop():
            return self.link.emergency_stop()

        return self._execute_safely("emergency_stop", _stop)

    def reset_robot(self) -> Dict[str, Any]:
        """复位机器人"""

        def _reset():
            return self.link.reset_robot()

        return self._execute_safely("reset_robot", _reset)

    # ============ 高级移动函数 ============
    def move_sequence(self, waypoints: List[Dict[str, Any]],
                      default_speed: float = 0.2) -> Dict[str, Any]:
        """执行一系列移动"""
        try:
            results = []
            for i, waypoint in enumerate(waypoints):
                move_type = waypoint.get("type", "joint")
                positions = waypoint.get("positions", [])
                speed = waypoint.get("speed", default_speed)

                logger.info(f"执行路径点 {i + 1}/{len(waypoints)}: {move_type}")

                if move_type == "joint":
                    result = self.test_move_j(positions, speed)
                elif move_type == "linear":
                    result = self.test_move_l(positions, speed)
                else:
                    result = {"status": "error", "error": f"未知移动类型: {move_type}"}

                results.append({"waypoint": i, "result": result})

                if result.get("status") != "ok":
                    logger.error(f"路径点 {i + 1} 执行失败，停止序列")
                    break

                # 短暂延迟确保运动完成
                time.sleep(0.5)

            return {
                "status": "ok",
                "total_waypoints": len(waypoints),
                "executed_waypoints": len(results),
                "results": results
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ============ 煎面包逻辑函数占位符 ============
    def pick_bread(self) -> Dict[str, Any]:
        """抓取面包 - 占位符"""
        logger.info("pick_bread: 功能占位符，暂未实现具体动作")
        # 这里将来会实现：
        # 1. 移动到面包位置上方
        # 2. 下降到抓取高度
        # 3. 关闭夹爪
        # 4. 提升
        return {
            "status": "ok",
            "message": "pick_bread占位符执行完成",
            "implemented": False,
            "todo": ["定义面包位置", "设计抓取轨迹", "配置夹爪参数"]
        }

    def place_on_pan(self) -> Dict[str, Any]:
        """将面包放到平底锅上 - 占位符"""
        logger.info("place_on_pan: 功能占位符，暂未实现具体动作")
        return {
            "status": "ok",
            "message": "place_on_pan占位符执行完成",
            "implemented": False,
            "todo": ["定义平底锅位置", "设计放置轨迹", "确保安全距离"]
        }

    def flip_bread(self) -> Dict[str, Any]:
        """翻转面包 - 占位符"""
        logger.info("flip_bread: 功能占位符，暂未实现具体动作")
        return {
            "status": "ok",
            "message": "flip_bread占位符执行完成",
            "implemented": False,
            "todo": ["设计翻转动作", "确保面包不掉落", "时间控制"]
        }

    def control_heating(self, enable: bool) -> Dict[str, Any]:
        """控制加热 - 占位符"""
        action = "开启" if enable else "关闭"
        logger.info(f"control_heating: {action}加热 - 功能占位符")
        return {
            "status": "ok",
            "message": f"control_heating({action})占位符执行完成",
            "implemented": False,
            "todo": ["连接加热设备", "定义控制信号", "安全保护"]
        }

    def toast_cycle(self, toast_time: int = 30) -> Dict[str, Any]:
        """完整的煎面包循环 - 占位符"""
        logger.info("toast_cycle: 开始煎面包循环占位符")

        # 占位符逻辑：模拟完整流程
        steps = [
            ("系统初始化", self.move_to_safe_position),
            ("抓取面包", self.pick_bread),
            ("放置到锅上", self.place_on_pan),
            ("开启加热", lambda: self.control_heating(True)),
            (f"等待{toast_time // 2}秒", lambda: {"status": "ok", "message": f"模拟等待{toast_time // 2}秒"}),
            ("翻转面包", self.flip_bread),
            (f"继续等待{toast_time // 2}秒", lambda: {"status": "ok", "message": f"模拟等待{toast_time // 2}秒"}),
            ("关闭加热", lambda: self.control_heating(False)),
            ("返回安全位置", self.move_to_safe_position)
        ]

        results = []
        for step_name, step_func in steps:
            logger.info(f"执行占位符步骤: {step_name}")
            result = step_func()
            results.append({"step": step_name, "result": result})

            # 如果是实际实现的函数失败，则停止
            if result.get("status") != "ok" and result.get("implemented", True):
                logger.error(f"步骤 '{step_name}' 失败，停止执行")
                return {
                    "status": "error",
                    "failed_step": step_name,
                    "completed_steps": len(results) - 1,
                    "results": results,
                    "note": "这是占位符测试，部分功能未实现"
                }

        logger.info("煎面包循环占位符完成")
        return {
            "status": "ok",
            "total_steps": len(steps),
            "toast_time": toast_time,
            "results": results,
            "note": "这是占位符测试，实际动作未执行",
            "implemented": False
        }