export function useUniqueName() {
  const generateUniqueName = (baseName: string, separator: string = ' '): string => {
    const timestamp = Date.now()
    return `${baseName}${separator}${timestamp}`
  }

  const generateShortUniqueName = (baseName: string, separator: string = ' '): string => {
    const timestamp = Date.now()
    const randomPart = Math.floor(Math.random() * 100)
    const uniqueSuffix = `${(timestamp % 1000).toString().padStart(3, '0')}${randomPart.toString().padStart(2, '0')}` // 3 timestamp + 2 random = 5 digits
    return `${baseName}${separator}${uniqueSuffix}`
  }

  return {
    generateUniqueName,
    generateShortUniqueName
  }
}
