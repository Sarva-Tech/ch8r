export const NEW_CHAT = 'new_chat'
export const DUMMY_NEW_CHATROOM = {
  uuid: NEW_CHAT,
  name: 'New Chat'
}

export const AVAILABLE_COLORS = [
  // { id: 'neutral', label: 'Neutral', preview: 'oklch(0.85 0.01 270)' },
  { id: 'gray', label: 'Gray', preview: 'oklch(0.72 0.01 270)' },
  { id: 'blue', label: 'Blue', preview: 'oklch(0.65 0.18 250)' },
  // { id: 'rose', label: 'Rose', preview: 'oklch(0.62 0.22 30)' },
  // { id: 'orange', label: 'Orange', preview: 'oklch(0.7927 0.171 70.67)' },
  // { id: 'green', label: 'Green', preview: 'oklch(0.86 0.29 142.49)' },
  // { id: 'yellow', label: 'Yellow', preview: 'oklch(0.968 0.211 109.77)'},
  { id: 'violet', label: 'Violet', preview: 'oklch(0.5294 0.293 293.6103)'},
]
export const DEFAULT_COLOR = AVAILABLE_COLORS[0]

export const SENDER_ID_PREFIX = 'reg'
