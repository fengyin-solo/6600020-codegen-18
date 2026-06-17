from pydantic import BaseModel
from typing import List, Optional

class ModbusRegister(BaseModel):
    address: int
    name: str
    type: str
    value: float
    unit: str

class Device(BaseModel):
    id: str
    name: str
    ip: str
    port: int
    slave_id: int
    online: bool
    registers: List[ModbusRegister] = []

class SelfCheckItem(BaseModel):
    name: str
    status: str
    message: str
    details: Optional[str] = None

class DeviceSelfCheckResult(BaseModel):
    device_id: str
    device_name: str
    overall_status: str
    connectivity_checks: List[SelfCheckItem]
    config_checks: List[SelfCheckItem]

class SelfCheckResponse(BaseModel):
    overall_status: str
    total_devices: int
    passed_devices: int
    failed_devices: int
    results: List[DeviceSelfCheckResult]
