<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-foreground">
          {{ title }}
        </h3>
        <USelect
          v-model="selectedPeriod"
          :options="periodOptions"
          size="sm"
          class="w-32"
        />
      </div>
    </template>

    <div class="space-y-4">
      <div class="h-64 relative">
        <canvas ref="chartCanvas" class="w-full h-full"></canvas>
      </div>

      <div class="flex flex-wrap gap-4 justify-center">
        <div
          v-for="item in legendItems"
          :key="item.label"
          class="flex items-center gap-2"
        >
          <div
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: item.color }"
          ></div>
          <span class="text-sm text-muted-foreground">
            {{ item.label }}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border">
        <div class="text-center">
          <div class="text-lg font-semibold text-foreground">
            {{ totalValue }}
          </div>
          <div class="text-xs text-muted-foreground">Total</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-primary">
            {{ averageValue }}
          </div>
          <div class="text-xs text-muted-foreground">Average</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-green-600 dark:text-green-400">
            {{ peakValue }}
          </div>
          <div class="text-xs text-muted-foreground">Peak</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-muted-foreground">
            {{ trendDirection }}
          </div>
          <div class="text-xs text-muted-foreground">Trend</div>
        </div>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
interface Props {
  title: string
  data: Array<{
    label: string
    value: number
    date?: string
  }>
  type?: 'line' | 'bar' | 'area'
  colors?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  type: 'line',
  colors: () => ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
})

const chartCanvas = ref<HTMLCanvasElement>()
const selectedPeriod = ref('7d')

const periodOptions = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
  { value: '1y', label: '1 year' }
]

const legendItems = computed(() => {
  if (props.data.length === 0) return []

  const uniqueLabels = [...new Set(props.data.map(d => d.label))]

  return uniqueLabels.map((label, index) => ({
    label,
    color: props.colors[index % props.colors.length]
  }))
})

const totalValue = computed(() => {
  return props.data.reduce((sum, item) => sum + item.value, 0).toLocaleString()
})

const averageValue = computed(() => {
  if (props.data.length === 0) return '0'
  const avg = props.data.reduce((sum, item) => sum + item.value, 0) / props.data.length
  return Math.round(avg).toLocaleString()
})

const peakValue = computed(() => {
  if (props.data.length === 0) return '0'
  const peak = Math.max(...props.data.map(item => item.value))
  return peak.toLocaleString()
})

const trendDirection = computed(() => {
  if (props.data.length < 2) return 'N/A'

  const recent = props.data.slice(-7) // Last 7 data points
  const older = props.data.slice(-14, -7) // Previous 7 data points

  if (older.length === 0) return 'N/A'

  const recentAvg = recent.reduce((sum, item) => sum + item.value, 0) / recent.length
  const olderAvg = older.reduce((sum, item) => sum + item.value, 0) / older.length

  if (recentAvg > olderAvg * 1.1) return '↑ Up'
  if (recentAvg < olderAvg * 0.9) return '↓ Down'
  return '→ Stable'
})

const drawChart = () => {
  if (!chartCanvas.value || props.data.length === 0) return

  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width
  canvas.height = rect.height

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const padding = 40
  const chartWidth = canvas.width - padding * 2
  const chartHeight = canvas.height - padding * 2

  const values = props.data.map(d => d.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const valueRange = maxValue - minValue || 1

  ctx.strokeStyle = '#E5E7EB'
  ctx.lineWidth = 1

  ctx.beginPath()
  ctx.moveTo(padding, padding)
  ctx.lineTo(padding, canvas.height - padding)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(padding, canvas.height - padding)
  ctx.lineTo(canvas.width - padding, canvas.height - padding)
  ctx.stroke()

  ctx.strokeStyle = '#F3F4F6'
  ctx.setLineDash([5, 5])

  for (let i = 0; i <= 5; i++) {
    const y = padding + (chartHeight / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(canvas.width - padding, y)
    ctx.stroke()
  }

  ctx.setLineDash([])

  const datasets = new Map<string, Array<{ value: number; index: number }>>()
  props.data.forEach((item, index) => {
    if (!datasets.has(item.label)) {
      datasets.set(item.label, [])
    }
    datasets.get(item.label)!.push({ value: item.value, index })
  })

  let datasetIndex = 0
  datasets.forEach((dataPoints, label) => {
    const color = props.colors[datasetIndex % props.colors.length]

    if (props.type === 'line' || props.type === 'area') {
      drawLineChart(ctx, dataPoints, color, chartWidth, chartHeight, padding, minValue, valueRange, props.type === 'area')
    } else if (props.type === 'bar') {
      drawBarChart(ctx, dataPoints, color, chartWidth, chartHeight, padding, minValue, valueRange, datasets.size)
    }

    datasetIndex++
  })

  ctx.fillStyle = '#6B7280'
  ctx.font = '12px sans-serif'

  for (let i = 0; i <= 5; i++) {
    const value = minValue + (valueRange / 5) * (5 - i)
    const y = padding + (chartHeight / 5) * i
    ctx.fillText(Math.round(value).toString(), 5, y + 4)
  }

  const labelCount = props.data.length
  const step = Math.max(1, Math.floor(labelCount / 10))

  props.data.forEach((item, index) => {
    if (index % step === 0) {
      const x = padding + (chartWidth / (labelCount - 1)) * index
      const label = item.date || item.label
      ctx.save()
      ctx.translate(x, canvas.height - padding + 15)
      ctx.rotate(-Math.PI / 4)
      ctx.fillText(label, 0, 0)
      ctx.restore()
    }
  })
}

const drawLineChart = (
  ctx: CanvasRenderingContext2D,
  dataPoints: Array<{ value: number; index: number }>,
  color: string,
  chartWidth: number,
  chartHeight: number,
  padding: number,
  minValue: number,
  valueRange: number,
  fillArea: boolean
) => {
  if (dataPoints.length === 0) return

  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.beginPath()

  dataPoints.forEach((point, index) => {
    const x = padding + (chartWidth / (props.data.length - 1)) * point.index
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })

  ctx.stroke()

  if (fillArea) {
    ctx.lineTo(padding + chartWidth, padding + chartHeight)
    ctx.lineTo(padding, padding + chartHeight)
    ctx.closePath()

    ctx.fillStyle = color + '20'
    ctx.fill()
  }

  ctx.fillStyle = color
  dataPoints.forEach((point) => {
    const x = padding + (chartWidth / (props.data.length - 1)) * point.index
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fill()
  })
}

const drawBarChart = (
  ctx: CanvasRenderingContext2D,
  dataPoints: Array<{ value: number; index: number }>,
  color: string,
  chartWidth: number,
  chartHeight: number,
  padding: number,
  minValue: number,
  valueRange: number,
  datasetCount: number
) => {
  if (dataPoints.length === 0) return

  const barWidth = (chartWidth / props.data.length) / datasetCount * 0.8
  const barSpacing = (chartWidth / props.data.length) * 0.2

  ctx.fillStyle = color

  dataPoints.forEach((point, index) => {
    const x = padding + (chartWidth / props.data.length) * point.index + barSpacing / 2
    const barHeight = ((point.value - minValue) / valueRange) * chartHeight
    const y = padding + chartHeight - barHeight

    ctx.fillRect(x, y, barWidth, barHeight)
  })
}

watch(() => [props.data, props.type, selectedPeriod.value], () => {
  nextTick(() => {
    drawChart()
  })
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    drawChart()
  })

  window.addEventListener('resize', drawChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', drawChart)
})
</script>
