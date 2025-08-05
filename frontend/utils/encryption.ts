import JSEncrypt from 'jsencrypt'

export const PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoJm1bzXEGxFnVgeJXABI
OwGbeUBevgAG0uZJISuJYPLjXUzY8XwDQ6CG7olLqzXXrvElHHbBUdPM8kWXADtY
dpGHbPc06Sicx3OVuYW/d/e2sIhQeu5aU+28i3Hc+QRvFGTbbAC12QKkVQ94Mc61
wiyWJBXIbj/zOa9ZihytdVMtUAXsjOC/VinYevgYApjP2iztcix4+59UgXRLWpwd
dqKc8yblS9vaV6LsdD4MCLQVCvQNITOsQrXxASo1qpdo8ow9j3mhPAf/sWg5Xp5C
QeGcUIpwg+F1aCJqVt38pNAw0BaKqRCLEY1jpYdQrE3IywhhEMSuaTmOPkPH3lng
kwIDAQAB
-----END PUBLIC KEY-----`


export const encryptWithPublicKey = (data: string, publicKey: string = PUBLIC_KEY): string => {
  const encrypt = new JSEncrypt()
  encrypt.setPublicKey(publicKey)
  const encrypted = encrypt.encrypt(data)
  if (!encrypted) {
    throw new Error('Encryption failed')
  }
  return encrypted
}
