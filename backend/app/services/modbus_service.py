"""Modbus service with mock data (replace with pymodbus for production)."""
import random
import re
import socket
from typing import List, Dict, Any, Tuple

MOCK_DEVICES = [
    {"id": "dev1", "name": "温湿度传感器-A区", "ip": "192.168.1.101", "port": 502, "slave_id": 1, "online": True},
    {"id": "dev2", "name": "压力变送器-B区", "ip": "192.168.1.102", "port": 502, "slave_id": 2, "online": True},
    {"id": "dev3", "name": "电机控制器-C区", "ip": "192.168.1.103", "port": 502, "slave_id": 3, "online": False},
]

MOCK_REGISTERS = {
    "dev1": [
        {"address": 0, "name": "温度", "type": "holding", "value": 25.6, "unit": "°C"},
        {"address": 1, "name": "湿度", "type": "holding", "value": 62.3, "unit": "%RH"},
        {"address": 2, "name": "露点", "type": "holding", "value": 17.8, "unit": "°C"},
    ],
    "dev2": [
        {"address": 0, "name": "管道压力", "type": "holding", "value": 3.45, "unit": "MPa"},
        {"address": 1, "name": "差压", "type": "holding", "value": 0.12, "unit": "kPa"},
    ],
    "dev3": [
        {"address": 0, "name": "转速", "type": "holding", "value": 1480, "unit": "RPM"},
        {"address": 1, "name": "电流", "type": "holding", "value": 12.5, "unit": "A"},
    ],
}

def get_device_status() -> List[Dict[str, Any]]:
    return MOCK_DEVICES

def read_registers(device_id: str, address: int, count: int) -> Dict[str, Any]:
    """Read registers via pymodbus (mock implementation)."""
    # In production: from pymodbus.client import ModbusTcpClient
    # client = ModbusTcpClient(host, port=port)
    # result = client.read_holding_registers(address, count, slave=slave_id)
    values = [round(random.uniform(0, 100), 2) for _ in range(count)]
    return {"device_id": device_id, "address": address, "values": values}

def _check_ip_format(ip: str) -> Tuple[bool, str]:
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if not ip:
        return False, "IP地址为空"
    if re.match(pattern, ip):
        return True, "IP地址格式正确"
    return False, f"IP地址格式无效: {ip}"

def _check_port_valid(port: int) -> Tuple[bool, str]:
    if not isinstance(port, int):
        return False, "端口必须为整数"
    if 1 <= port <= 65535:
        return True, "端口号有效"
    return False, f"端口号超出有效范围(1-65535): {port}"

def _check_slave_id_valid(slave_id: int) -> Tuple[bool, str]:
    if not isinstance(slave_id, int):
        return False, "Slave ID必须为整数"
    if 1 <= slave_id <= 247:
        return True, "Slave ID有效"
    return False, f"Slave ID超出有效范围(1-247): {slave_id}"

def _check_port_connectivity(ip: str, port: int, timeout: float = 2.0) -> Tuple[bool, str]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            return True, f"端口 {port} 可访问"
        return False, f"端口 {port} 不可访问 (错误码: {result})"
    except socket.gaierror:
        return False, f"无法解析主机地址: {ip}"
    except socket.timeout:
        return False, f"连接超时 ({timeout}s)"
    except Exception as e:
        return False, f"连接异常: {str(e)}"

def _check_modbus_communication(ip: str, port: int, slave_id: int) -> Tuple[bool, str]:
    # In production: use pymodbus to read a test register
    device = next((d for d in MOCK_DEVICES if d["ip"] == ip and d["port"] == port and d["slave_id"] == slave_id), None)
    if device and device["online"]:
        return True, "Modbus通信正常"
    return False, "Modbus通信失败，设备离线或无响应"

def _check_device_config(device: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = []

    ip_ok, ip_msg = _check_ip_format(device.get("ip", ""))
    checks.append({"name": "IP地址格式", "status": "passed" if ip_ok else "failed", "message": ip_msg})

    port_ok, port_msg = _check_port_valid(device.get("port", 0))
    checks.append({"name": "端口有效性", "status": "passed" if port_ok else "failed", "message": port_msg})

    slave_ok, slave_msg = _check_slave_id_valid(device.get("slave_id", 0))
    checks.append({"name": "Slave ID有效性", "status": "passed" if slave_ok else "failed", "message": slave_msg})

    registers = MOCK_REGISTERS.get(device["id"], [])
    if len(registers) > 0:
        checks.append({"name": "采集寄存器配置", "status": "passed", "message": f"已配置 {len(registers)} 个采集寄存器"})
    else:
        checks.append({"name": "采集寄存器配置", "status": "failed", "message": "未配置任何采集寄存器"})

    return checks

def _check_device_connectivity(device: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = []

    ip_ok, _ = _check_ip_format(device.get("ip", ""))
    port_ok, _ = _check_port_valid(device.get("port", 0))

    if ip_ok and port_ok:
        conn_ok, conn_msg = _check_port_connectivity(device["ip"], device["port"])
        checks.append({"name": "TCP端口连通性", "status": "passed" if conn_ok else "failed", "message": conn_msg})

        if conn_ok:
            mb_ok, mb_msg = _check_modbus_communication(device["ip"], device["port"], device.get("slave_id", 0))
            checks.append({"name": "Modbus通信测试", "status": "passed" if mb_ok else "failed", "message": mb_msg})
        else:
            checks.append({"name": "Modbus通信测试", "status": "skipped", "message": "跳过（端口不可达）"})
    else:
        checks.append({"name": "TCP端口连通性", "status": "skipped", "message": "跳过（IP或端口无效）"})
        checks.append({"name": "Modbus通信测试", "status": "skipped", "message": "跳过（IP或端口无效）"})

    return checks

def run_self_check() -> Dict[str, Any]:
    """Run self-check for all devices before data collection."""
    results = []
    passed = 0
    failed = 0

    for device in MOCK_DEVICES:
        config_checks = _check_device_config(device)
        connectivity_checks = _check_device_connectivity(device)

        all_checks = config_checks + connectivity_checks
        has_failure = any(c["status"] == "failed" for c in all_checks)

        if has_failure:
            failed += 1
            overall = "failed"
        else:
            passed += 1
            overall = "passed"

        results.append({
            "device_id": device["id"],
            "device_name": device["name"],
            "overall_status": overall,
            "connectivity_checks": connectivity_checks,
            "config_checks": config_checks,
        })

    total = len(MOCK_DEVICES)
    overall_status = "passed" if failed == 0 else ("partial" if passed > 0 else "failed")

    return {
        "overall_status": overall_status,
        "total_devices": total,
        "passed_devices": passed,
        "failed_devices": failed,
        "results": results,
    }
