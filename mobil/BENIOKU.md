# Agora mobil uygulaması

Bu klasör Agora'nın Android (ve istenirse iOS) uygulamasıdır. Uygulama [Capacitor](https://capacitorjs.com) ile
yapılmış yerel bir kabuktur: açılınca Agora'nın sitesini tam ekran açar. Web sitesiyle aynı sayfaları, hesabı
ve veritabanını kullanır; sitedeki değişiklikler uygulamaya ayrıca güncelleme gerektirmeden yansır.

Uygulamaya özel olanlar:

- Telefonda alt sekme çubuğu (Konular, Oylamalar, yeni konu, Meclis, Panelim). Aynı çubuk telefon tarayıcısında da görünür.
- Durum çubuğu ve çentik boşlukları (`--safe-area-inset-*`) sayfa düzenine eklenir.
- Geri tuşu önce sayfa geçmişinde geri gider, geçmiş bitince uygulamayı kapatır (`@capacitor/app` ve `forum/static/app.js`).
- Bağlantı yoksa “Bağlantı kurulamadı” ekranı ve “Tekrar dene” düğmesi çıkar (`www/hata.html`).
- Tarayıcı kimliğinin sonunda `AgoraMobil` yazar; site, uygulamada açıldığını buradan anlar.

## Hazır APK

Uygulama varsayılan olarak Agora'nın web sitesini (<https://baki-b.github.io/YZM327-Odevler/>) açar; sunucu gerekmez.
`main` dalına her gönderimde GitHub Actions (`.github/workflows/android.yml`) APK'yı derleyip **Releases** sayfasına
koyar: [Agora.apk](https://github.com/Baki-B/YZM327-Odevler/releases/latest/download/Agora.apk). Telefonda bu
bağlantıyı açıp dosyayı indir ve kur (Android "bilinmeyen kaynaklardan yükleme" izni ister).

## Kendin derlemek

Gerekenler: Node.js 20 veya üstü ve [Android Studio](https://developer.android.com/studio) (Android SDK ve Java onunla gelir).

```bash
npm install
npm run esitle
npm run android
```

Android Studio'da ▶ ile telefona ya da emülatöre kurulur. APK dosyası için **Build › Build App Bundle(s) / APK(s) › Build APK(s)**;
dosya `android/app/build/outputs/apk/debug/app-debug.apk` olarak çıkar.

**Kendi sunucuna bağlamak:** proje klasöründe `python calistir.py --ag` ile forumu başlat; ekrana
`Telefondan (aynı Wi-Fi): http://192.168.x.x:5000` gibi bir adres yazar. Sonra bu klasörde:

```bash
npm run adres -- http://192.168.x.x:5000
npm run esitle
```

Android emülatöründe bilgisayarın adresi `http://10.0.2.2:5000` olur. Web sitesine geri dönmek için
`npm run adres -- https://baki-b.github.io/YZM327-Odevler/`.

## Anlık bildirim (isteğe bağlı)

Uygulama kapalıyken de bildirim gelmesi için Firebase Cloud Messaging kullanılır. Ücretsizdir ama bir kez ayarlamak gerekir:

1. [Firebase konsolunda](https://console.firebase.google.com) bir proje aç ve **Android uygulaması ekle** seçeneğiyle uygulamayı ekle.
   Paket adı: `com.agora.forum`.
2. İndirilen `google-services.json` dosyasını `mobil/android/app/` klasörüne koy.
3. Firebase konsolunda **Proje ayarları › Hizmet hesapları › Yeni özel anahtar oluştur** ile bir JSON dosyası indir,
   adını `firebase.json` yapıp sunucudaki `instance/` klasörüne koy. Bu dosya gizlidir; kimseyle paylaşma.
4. Sunucuda `pip install pywebpush==2.5.0` çalıştır (imza için gereken kütüphaneyi de kurar), sunucuyu yeniden başlat.
5. Bu klasörde `npm run esitle`, sonra Android Studio'da uygulamayı yeniden derle.

Sonra uygulamada **Panelim › Bildirimler › Bu cihazda aç**. Bildirime dokununca ilgili sayfa açılır.
Tarayıcıdaki anlık bildirim için Firebase gerekmez; yalnızca `pip install pywebpush==2.5.0` yeter (site HTTPS adreste olmalı).

## iOS

iOS uygulaması için bir Mac ve Xcode gerekir. Mac'te bu klasörde `npm install @capacitor/ios`, `npx cap add ios` ve
`npx cap open ios` komutlarını çalıştır; ayarlar (`capacitor.config.json`) aynıdır.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `capacitor.config.json` | Uygulama adı ve kimliği, sunucu adresi, tarayıcı kimliği eki, kenar boşlukları |
| `adres.js` | `npm run adres` komutu: sunucu adresini değiştirir |
| `@capacitor/push-notifications` | Anlık bildirim (Firebase ayarlanınca çalışır) |
| `www/hata.html` | Sunucuya ulaşılamayınca görünen ekran |
| `android/` | Android Studio projesi (simgeler ve açılış ekranı forumun simgesinden üretildi) |
