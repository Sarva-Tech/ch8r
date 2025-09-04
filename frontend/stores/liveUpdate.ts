import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
const config = useRuntimeConfig()

type SocketMessage = {
  type: string
  data: never
}

type Listener = (data: SocketMessage) => void

export const useLiveUpdateStore = defineStore('liveUpdate', () => {
  const userStore = useUserStore()

  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const listeners = reactive(new Set<Listener>())
  const clientId = ref<string | null>(null)

  function connect(id: string) {
    if (socket.value) return
    clientId.value = id

    const wsProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://'
    const wsUrl = `${wsProtocol}${config.public.domain}/ws/updates/${userStore.userIdentifier}/`

    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      isConnected.value = true
      console.info('Connection to live updates established.')
    }

    socket.value.onclose = () => {
      isConnected.value = false
      socket.value = null
      console.warn('Connection to live updates disconnected.')
    }

    socket.value.onerror = (err) => {
      console.error(
        'Error establishing connection to receive live updates.',
        err,
      )
    }

    socket.value.onmessage = (event: MessageEvent) => {
      try {
        const data: SocketMessage = JSON.parse(event.data)
        listeners.forEach((cb) => cb(data))
      } catch (error) {
        console.error('Error parsing live update message', error)
      }
    }
  }

  function subscribe(callback: Listener): () => void {
    listeners.add(callback)
    return () => listeners.delete(callback)
  }

  return {
    connect,
    subscribe,
    isConnected,
  }
})
