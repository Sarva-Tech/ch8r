export function useTextUtils() {
  function ellipsis(text: string, maxLength = 100): string {
    if (!text) return ''
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
  }

  return { ellipsis }
}
