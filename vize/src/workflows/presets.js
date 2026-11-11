// Hazır desen kümeleri (yazılım mühendisliğinde sık aranan şeyler).
export const PRESETS = {
  // Kodda bırakılmış iş notları
  todo: { patterns: ['TODO', 'FIXME', 'HACK', 'XXX'], ignoreCase: false },
  // Koda gömülmüş gizli bilgi belirtileri (büyük/küçük harf duyarsız)
  secrets: {
    patterns: ['password=', 'passwd', 'secret_key', 'api_key', 'apikey', 'BEGIN RSA PRIVATE KEY', 'BEGIN OPENSSH PRIVATE KEY', 'AKIA', 'token='],
    ignoreCase: true,
  },
  // Güvenlik açısından riskli ya da yasaklanmış API çağrıları
  'banned-api': {
    patterns: ['eval(', 'exec(', 'pickle.loads', 'os.system(', 'subprocess.call(', 'innerHTML', 'document.write(', 'new Function('],
    ignoreCase: false,
  },
  // Log dosyalarında hata satırları
  errors: { patterns: ['ERROR', 'FATAL', 'Traceback', 'Exception', 'panic:'], ignoreCase: false },
};
