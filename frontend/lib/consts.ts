export const NEW_CHAT = 'new_chat'
export const DUMMY_NEW_CHATROOM = {
  uuid: NEW_CHAT,
  name: 'New Chat'
}

export const AVAILABLE_COLORS = [
  { id: 'neutral', label: 'Neutral', preview: 'oklch(0.85 0.01 270)' }, // soft gray-blue
  { id: 'gray', label: 'Gray', preview: 'oklch(0.72 0.01 270)' },
  { id: 'blue', label: 'Blue', preview: 'oklch(0.65 0.18 250)' },
  { id: 'rose', label: 'Rose', preview: 'oklch(0.62 0.22 30)' },
]
export const DEFAULT_COLOR = AVAILABLE_COLORS[0]
