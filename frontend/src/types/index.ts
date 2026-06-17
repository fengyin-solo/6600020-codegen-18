export interface ModbusRegister {
  address: number
  name: string
  type: 'coil' | 'discrete' | 'holding' | 'input'
  value: number | boolean
  unit: string
  updatedAt: number
}

export interface Device {
  id: string
  name: string
  ip: string
  port: number
  slaveId: number
  online: boolean
  registers: ModbusRegister[]
}

export interface Alarm {
  id: string
  deviceId: string
  register: string
  message: string
  level: 'info' | 'warning' | 'critical'
  timestamp: number
  acknowledged: boolean
}

export interface SelfCheckItem {
  name: string
  status: 'passed' | 'failed' | 'skipped'
  message: string
  details?: string
}

export interface DeviceSelfCheckResult {
  deviceId: string
  deviceName: string
  overallStatus: 'passed' | 'failed'
  connectivityChecks: SelfCheckItem[]
  configChecks: SelfCheckItem[]
}

export interface SelfCheckResponse {
  overallStatus: 'passed' | 'failed' | 'partial'
  totalDevices: number
  passedDevices: number
  failedDevices: number
  results: DeviceSelfCheckResult[]
}
