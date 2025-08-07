import JSEncrypt from 'jsencrypt'

const config = useRuntimeConfig()
const PUBLIC_KEY = config.public.NUXT_PUBLIC_KEY

export const encryptWithPublicKey = (data: string): string => {
  const encrypt = new JSEncrypt()
  encrypt.setPublicKey(PUBLIC_KEY)
  const encrypted = encrypt.encrypt(data)
  if (!encrypted) {
    throw new Error('Encryption failed')
  }
  return encrypted
}
