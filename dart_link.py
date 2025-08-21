"""


- `DartLink` class encapsulates all communication logic with the DART Studio server.
- Includes connection, disconnection, authentication, and message handling.
- Provides basic robot control functions (MoveJ, MoveL, IO control, emergency stop, state queries, etc.).


使用方式 / 사용 방법 / Usage:
----------------------
1. 创建对象 / 객체 생성 / Create an object:
```python
link = DartLink(host="192.168.10.10", port=9000, token="YOUR_TOKEN")
```


2. 建立连接 / 연결 / Connect:
```python
link.connect()
```


3. 调用函数发送指令 / 함수 호출로 명령 전송 / Call functions to send commands:
```python
link.move_j([0,0,0,0,0,0], speed=0.2) # 关节移动 / 관절 이동 / Joint movement
link.get_current_pose() # 获取位姿 / 현재 자세 / Get pose
```


4. 断开连接 / 연결 해제 / Disconnect:
```python
link.disconnect()
```


数据格式 / 데이터 형식 / Data format:
----------------------
所有消息均为 JSON 格式，以换行符 (\n) 分隔。
每条消息结构如下：
```json
{
"token": "认证令牌 / 인증 토큰 / authentication token",
"type": "消息类型 / 메시지 유형 / message type",
"function": "调用的函数名 / 호출 함수명 / function name",
"args": { "参数": "值" }
}
```


All messages are in JSON format, separated by newline (\n). Each message has the structure above.


函数说明 / 함수 설명 / Function descriptions:
----------------------
- `connect()` 建立连接 / 연결 / Establish connection
- `disconnect()` 断开连接 / 연결 해제 / Disconnect
- `ping()` 测试连接 / 연결 테스트 / Test connection
- `call()` 调用服务端函数 / 서버 함수 호출 / Call a server function
- `sequence()` 执行命令序列 / 명령 시퀀스 실행 / Execute sequence of commands
- `move_j()` 关节空间移动 / 관절 공간 이동 / Joint space movement
- `move_l()` 笛卡尔空间直线移动 / 데카르트 공간 직선 이동 / Cartesian linear movement
- `set_digital_output()` 设置数字输出 / 디지털 출력 설정 / Set digital output
- `get_digital_input()` 获取数字输入 / 디지털 입력 가져오기 / Get digital input
- `wait_ms()` 等待毫秒 / 밀리초 대기 / Wait milliseconds
- `get_current_pose()` 获取当前位姿 / 현재 자세 가져오기 / Get current pose
- `get_joint_angles()` 获取当前关节角度 / 현재 관절 각도 가져오기 / Get joint angles
- `emergency_stop()` 紧急停止 / 비상 정지 / Emergency stop
- `reset_robot()` 复位机器人 / 로봇 초기화 / Reset robot
- `get_robot_state()` 获取机器人状态 / 로봇 상태 가져오기 / Get robot state


"""
import socket
import json
import time
import logging
from typing import Dict, List, Any, Optional

DEFAULT_HOST = "127.0.0.1"  # 默认本地测试 / 로컬 테스트 기본값 / Default for local testing
DEFAULT_PORT = 9000  # 默认端口 / 기본 포트 / Default port
DEFAULT_TOKEN = "TEST_TOKEN_123"  # 默认认证令牌 / 기본 인증 토큰 / Default authentication token

# 配置日志 / 로그 설정 / Logging configuration
logger = logging.getLogger(__name__)


class DartLinkException(Exception):
    """DART通信异常 / DART 통신 예외 / DART communication exception"""
    pass


class DartLink:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 token: str = DEFAULT_TOKEN, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout
        self.socket = None
        self.connected = False

    def connect(self) -> bool:
        """建立持久连接 / 영구 연결 설정 / Establish persistent connection"""
        try:
            self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connected = True
            logger.info(f"已连接到 {self.host}:{self.port} / {self.host}:{self.port} 에 연결됨 / Connected to {self.host}:{self.port}")

            # 发送认证 / 인증 전송 / Send authentication
            auth_result = self._send_recv_internal({"token": self.token, "type": "auth"})
            if auth_result.get("status") != "ok":
                raise DartLinkException(f"认证失败: {auth_result} / 인증 실패: {auth_result} / Authentication failed: {auth_result}")

            return True
        except Exception as e:
            self.connected = False
            logger.error(f"连接失败: {e} / 연결 실패: {e} / Connection failed: {e}")
            return False

    def disconnect(self):
        """断开连接 / 연결 해제 / Disconnect"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.connected = False

    def _send_recv_internal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """内部发送接收函数 / 내부 송수신 함수 / Internal send-receive function"""
        if not self.socket:
            raise DartLinkException("未连接到服务器 / 서버에 연결되지 않음 / Not connected to server")

        data = json.dumps(payload) + "\n"

        try:
            # 发送数据 / 데이터 전송 / Send data
            self.socket.sendall(data.encode("utf-8"))
            logger.debug(f"发送: {payload} / 전송: {payload} / Sent: {payload}")

            # 接收响应 / 응답 수신 / Receive response
            buf = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    raise DartLinkException("连接已断开 / 연결이 끊어짐 / Connection closed")
                buf += chunk
                if b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    response = json.loads(line.decode("utf-8"))
                    logger.debug(f"接收: {response} / 수신: {response} / Received: {response}")
                    return response

        except (socket.error, json.JSONDecodeError) as e:
            self.connected = False
            raise DartLinkException(f"通信失败: {e} / 통신 실패: {e} / Communication failed: {e}")

    def _send_recv(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求并接收响应（带自动重连） / 요청 전송 및 응답 수신 (자동 재연결 포함) / Send request and receive response (with auto-reconnect)"""
        if not self.connected:
            if not self.connect():
                raise DartLinkException("无法建立连接 / 연결을 설정할 수 없음 / Cannot establish connection")

        try:
            return self._send_recv_internal(payload)
        except DartLinkException as e:
            # 连接断开，尝试重连一次 / 연결 끊김, 한 번 재연결 시도 / Connection lost, try reconnect once
            if "连接已断开" in str(e) or "通信失败" in str(e):
                logger.warning("连接断开，尝试重连... / 연결 끊김, 재연결 시도 중... / Connection lost, retrying...")
                self.disconnect()
                if self.connect():
                    return self._send_recv_internal(payload)
            raise e

    def ping(self) -> bool:
        """测试连接 / 연결 테스트 / Test connection"""
        try:
            resp = self._send_recv({"token": self.token, "type": "ping"})
            return resp.get("status") == "ok" and resp.get("pong") is True
        except Exception as e:
            logger.error(f"Ping失败: {e} / Ping 실패: {e} / Ping failed: {e}")
            return False

    def call(self, function: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调用单个函数 / 단일 함수 호출 / Call a single function"""
        payload = {
            "token": self.token,
            "type": "call",
            "function": function,
            "args": args or {}
        }
        logger.info(f"调用函数: {function} / 함수 호출: {function} / Calling function: {function}")
        return self._send_recv(payload)

    def sequence(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行命令序列 / 명령 시퀀스 실행 / Execute sequence of commands"""
        payload = {
            "token": self.token,
            "type": "sequence",
            "commands": commands
        }
        logger.info(f"执行命令序列，共 {len(commands)} 个命令 / 명령 시퀀스 실행, 총 {len(commands)}개 명령 / Executing command sequence with {len(commands)} commands")
        return self._send_recv(payload)

    # 基础机械臂控制函数 / 기본 로봇 제어 함수 / Basic robot control functions
    def move_j(self, positions: List[float], speed: float = 0.2) -> Dict[str, Any]:
        """关节空间移动 / 관절 공간 이동 / Joint space movement"""
        if len(positions) != 6:
            raise ValueError("关节位置必须包含6个值 / 관절 위치는 6개의 값이 필요함 / Joint positions must contain 6 values")
        if not (0.01 <= speed <= 1.0):
            raise ValueError("速度必须在0.01-1.0之间 / 속도는 0.01~1.0 사이여야 함 / Speed must be between 0.01 and 1.0")
        return self.call("MoveJ", {"positions": positions, "speed": speed})

    def move_l(self, positions: List[float], speed: float = 0.2) -> Dict[str, Any]:
        """笛卡尔空间直线移动 / 데카르트 공간 직선 이동 / Cartesian space linear movement"""
        if len(positions) != 6:
            raise ValueError("位姿必须包含6个值[x,y,z,rx,ry,rz] / 자세는 6개의 값[x,y,z,rx,ry,rz]이 필요함 / Pose must contain 6 values [x,y,z,rx,ry,rz]")
        if not (0.01 <= speed <= 1.0):
            raise ValueError("速度必须在0.01-1.0之间 / 속도는 0.01~1.0 사이여야 함 / Speed must be between 0.01 and 1.0")
        return self.call("MoveL", {"positions": positions, "speed": speed})

    def set_digital_output(self, pin: int, value: bool) -> Dict[str, Any]:
        """设置数字输出 / 디지털 출력 설정 / Set digital output"""
        return self.call("SetDO", {"pin": pin, "value": value})

    def get_digital_input(self, pin: int) -> Dict[str, Any]:
        """获取数字输入 / 디지털 입력 가져오기 / Get digital input"""
        return self.call("GetDI", {"pin": pin})

    def wait_ms(self, ms: int) -> Dict[str, Any]:
        """等待毫秒 / 밀리초 대기 / Wait milliseconds"""
        return self.call("WaitMs", {"ms": ms})

    def get_current_pose(self) -> Dict[str, Any]:
        """获取当前位姿 / 현재 자세 가져오기 / Get current pose"""
        return self.call("GetCurrentPose", {})

    def get_joint_angles(self) -> Dict[str, Any]:
        """获取当前关节角度 / 현재 관절 각도 가져오기 / Get current joint angles"""
        return self.call("GetJointAngles", {})

    def emergency_stop(self) -> Dict[str, Any]:
        """紧急停止 / 비상 정지 / Emergency stop"""
        return self.call("EmergencyStop", {})

    def reset_robot(self) -> Dict[str, Any]:
        """复位机器人 / 로봇 초기화 / Reset robot"""
        return self.call("ResetRobot", {})

    def get_robot_state(self) -> Dict[str, Any]:
        """获取机器人状态 / 로봇 상태 가져오기 / Get robot state"""
        return self.call("GetRobotState", {})

    def __enter__(self):
        """上下文管理器入口 / 컨텍스트 매니저 진입 / Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 / 컨텍스트 매니저 종료 / Context manager exit"""
        self.disconnect()
