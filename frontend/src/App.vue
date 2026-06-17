<template>
  <div class="flex h-screen">
    <!-- Sidebar -->
    <div class="w-64 bg-gray-900 p-4 flex flex-col gap-3 border-r border-gray-800 overflow-y-auto">
      <h1 class="text-lg font-bold text-orange-400">Modbus 工业监控</h1>
      <div class="flex gap-2">
        <button @click="handleStartPoll" :disabled="store.isPolling || store.isSelfChecking" class="flex-1 bg-green-700 py-1.5 rounded text-xs hover:bg-green-600 disabled:opacity-50">
          {{ store.isSelfChecking ? '自检中...' : store.isPolling ? '采集中...' : '开始采集' }}
        </button>
        <button @click="stopPoll" :disabled="!store.isPolling" class="flex-1 bg-red-700 py-1.5 rounded text-xs hover:bg-red-600 disabled:opacity-50">
          停止
        </button>
      </div>
      <div>
        <label class="text-gray-400 text-xs">轮询间隔: {{ store.pollInterval }}ms</label>
        <input type="range" v-model.number="store.pollInterval" min="200" max="5000" step="100" class="w-full" />
      </div>

      <h3 class="text-gray-400 text-xs mt-2">设备列表</h3>
      <div v-for="d in store.devices" :key="d.id" @click="store.selectedDevice = d"
        class="bg-gray-800 rounded p-2 cursor-pointer text-sm"
        :class="store.selectedDevice?.id === d.id ? 'ring-1 ring-orange-500' : ''">
        <div class="flex justify-between">
          <span>{{ d.name }}</span>
          <span class="w-2 h-2 rounded-full mt-1.5" :class="d.online ? 'bg-green-500' : 'bg-red-500'"></span>
        </div>
        <div class="text-xs text-gray-500">{{ d.ip }}:{{ d.port }} [{{ d.slaveId }}]</div>
      </div>

      <div v-if="store.criticalAlarms.length" class="bg-red-900/50 rounded p-2 mt-2">
        <h4 class="text-red-400 text-xs font-bold">⚠ 严重告警 {{ store.criticalAlarms.length }}</h4>
        <div v-for="a in store.criticalAlarms.slice(0, 3)" :key="a.id" class="text-xs text-red-300 mt-1 truncate">
          {{ a.message }}
        </div>
      </div>

      <div class="text-xs text-gray-600 mt-auto">
        在线: {{ store.onlineDevices.length }}/{{ store.devices.length }}
      </div>
    </div>

    <!-- Main Dashboard -->
    <div class="flex-1 flex flex-col gap-3 p-4 overflow-y-auto">
      <!-- Register Gauges -->
      <div class="grid grid-cols-4 gap-3">
        <template v-for="d in store.devices" :key="d.id">
          <div v-for="r in d.registers" :key="`${d.id}_${r.address}`"
            class="bg-gray-900 rounded-xl p-3">
            <div class="text-xs text-gray-400">{{ d.name }}</div>
            <div class="text-2xl font-bold" :class="d.online ? 'text-orange-400' : 'text-gray-600'">
              {{ typeof r.value === 'number' ? r.value.toFixed(r.value > 100 ? 0 : 1) : r.value ? 'ON' : 'OFF' }}
            </div>
            <div class="text-xs text-gray-500">{{ r.name }} {{ r.unit }}</div>
          </div>
        </template>
      </div>

      <!-- Chart -->
      <div class="bg-gray-900 rounded-xl p-3 flex-1">
        <h3 class="text-sm text-gray-400 mb-2">
          实时趋势 — {{ store.selectedDevice?.name || '选择设备' }}
        </h3>
        <TrendChart />
      </div>

      <!-- Alarm List -->
      <div class="bg-gray-900 rounded-xl p-3 max-h-48 overflow-y-auto">
        <h3 class="text-sm text-gray-400 mb-2">告警记录</h3>
        <div v-for="a in store.alarms.slice(0, 10)" :key="a.id"
          class="flex justify-between text-xs bg-gray-800 rounded p-2 mb-1"
          :class="{ 'border-l-4 border-red-500': a.level === 'critical', 'border-l-4 border-yellow-500': a.level === 'warning' }">
          <span>{{ a.message }}</span>
          <div class="flex gap-2">
            <span class="text-gray-500">{{ new Date(a.timestamp).toLocaleTimeString() }}</span>
            <button v-if="!a.acknowledged" @click="store.acknowledgeAlarm(a.id)" class="text-blue-400 hover:underline">确认</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Self-check Dialog -->
    <div v-if="store.showSelfCheckDialog && store.selfCheckResult" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div class="bg-gray-900 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-bold" :class="{
            'text-green-400': store.selfCheckResult.overallStatus === 'passed',
            'text-yellow-400': store.selfCheckResult.overallStatus === 'partial',
            'text-red-400': store.selfCheckResult.overallStatus === 'failed'
          }">
            {{ overallStatusText }}
          </h2>
          <span class="text-sm text-gray-400">
            {{ store.selfCheckResult.passedDevices }}/{{ store.selfCheckResult.totalDevices }} 设备通过
          </span>
        </div>

        <div v-for="result in store.selfCheckResult.results" :key="result.deviceId" class="mb-4 bg-gray-800 rounded-lg p-4">
          <div class="flex justify-between items-center mb-2">
            <h3 class="font-medium">{{ result.deviceName }}</h3>
            <span class="text-xs px-2 py-0.5 rounded" :class="{
              'bg-green-900/50 text-green-400': result.overallStatus === 'passed',
              'bg-red-900/50 text-red-400': result.overallStatus === 'failed'
            }">
              {{ result.overallStatus === 'passed' ? '通过' : '失败' }}
            </span>
          </div>

          <div class="space-y-3">
            <div>
              <h4 class="text-xs text-gray-400 mb-1">🔧 配置检查</h4>
              <div v-for="check in result.configChecks" :key="check.name" class="flex items-center gap-2 text-xs py-0.5">
                <span class="w-4 h-4 flex items-center justify-center" :class="{
                  'text-green-400': check.status === 'passed',
                  'text-red-400': check.status === 'failed',
                  'text-gray-500': check.status === 'skipped'
                }">
                  {{ check.status === 'passed' ? '✓' : check.status === 'failed' ? '✗' : '→' }}
                </span>
                <span class="text-gray-300">{{ check.name }}:</span>
                <span :class="{
                  'text-green-400': check.status === 'passed',
                  'text-red-400': check.status === 'failed',
                  'text-gray-500': check.status === 'skipped'
                }">{{ check.message }}</span>
              </div>
            </div>

            <div>
              <h4 class="text-xs text-gray-400 mb-1">🌐 连通性检查</h4>
              <div v-for="check in result.connectivityChecks" :key="check.name" class="flex items-center gap-2 text-xs py-0.5">
                <span class="w-4 h-4 flex items-center justify-center" :class="{
                  'text-green-400': check.status === 'passed',
                  'text-red-400': check.status === 'failed',
                  'text-gray-500': check.status === 'skipped'
                }">
                  {{ check.status === 'passed' ? '✓' : check.status === 'failed' ? '✗' : '→' }}
                </span>
                <span class="text-gray-300">{{ check.name }}:</span>
                <span :class="{
                  'text-green-400': check.status === 'passed',
                  'text-red-400': check.status === 'failed',
                  'text-gray-500': check.status === 'skipped'
                }">{{ check.message }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-2 mt-4">
          <template v-if="store.selfCheckResult.overallStatus === 'passed'">
            <button @click="confirmAndStartPoll" class="flex-1 bg-green-700 py-2 rounded text-sm hover:bg-green-600">
              开始采集
            </button>
            <button @click="store.closeSelfCheckDialog()" class="flex-1 bg-gray-700 py-2 rounded text-sm hover:bg-gray-600">
              取消
            </button>
          </template>
          <template v-else>
            <button @click="confirmAndStartPoll" class="flex-1 bg-yellow-700 py-2 rounded text-sm hover:bg-yellow-600">
              强制开始（忽略警告）
            </button>
            <button @click="store.closeSelfCheckDialog()" class="flex-1 bg-gray-700 py-2 rounded text-sm hover:bg-gray-600">
              取消
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useModbusStore } from './store/modbus'
import TrendChart from './components/TrendChart.vue'

const store = useModbusStore()
let timer: number | null = null

const overallStatusText = computed(() => {
  if (!store.selfCheckResult) return ''
  switch (store.selfCheckResult.overallStatus) {
    case 'passed': return '✅ 采集前自检全部通过'
    case 'partial': return '⚠️ 部分设备自检未通过'
    case 'failed': return '❌ 采集前自检失败'
    default: return '采集前自检'
  }
})

async function handleStartPoll() {
  const passed = await store.runSelfCheck()
  if (passed) {
    confirmAndStartPoll()
  }
}

function confirmAndStartPoll() {
  store.closeSelfCheckDialog()
  startPoll()
}

function startPoll() {
  store.isPolling = true
  timer = window.setInterval(() => store.simulatePoll(), store.pollInterval)
}

function stopPoll() {
  store.isPolling = false
  if (timer) { clearInterval(timer); timer = null }
}

onMounted(() => store.initMockDevices())
onUnmounted(() => stopPoll())
</script>
