# Agora mobil uygulaması

Bu klasör Agora'nın Android (ve istenirse iOS) uygulamasıdır. Uygulama [Capacitor](https://capacitorjs.com) ile
yapılmış yerel bir kabuktur: açılınca Agora sunucusundaki siteyi tam ekran açar. Bu yüzden web sitesiyle aynı sayfaları,
aynı hesabı ve aynı veritabanını kullanır. Sitede yapılan her değişiklik uygulamaya da yansır; ayrıca güncelleme gerekmez.

Uygulamaya özel olanlar:

- Telefonda alt sekme çubuğu (Konular, Oylamalar, yeni konu, Meclis, Panelim). Aynı çubuk telefon tarayıcısında da görünür.
- Durum çubuğu ve çentik boşlukları (`--safe-area-inset-*`) sayfa düzenine eklenir.
- Geri tuşu önce sayfa geçmişinde geri gider, geçmiş bitince uygulamayı kapatır (`@capacitor/app` ve `forum/static/app.js`).
- Sunucuya ulaşılamazsa “Sunucuya bağlanılamadı” ekranı ve “Tekrar dene” düğmesi çıkar (`www/hata.html`).
- Tarayıcı kimliğinin sonunda `AgoraMobil` yazar; site, uygulamada açıldığını buradan anlar.

## Gerekenler

- Node.js 20 veya üstü
- [Android Studio](https://developer.android.com/studio) (Android SDK ve Java onunla birlikte gelir)

## APK oluşturma

1. Forumu ağa açık başlat (proje klasöründe):

   ```bash
   python calistir.py --ag
   ```

   Ekranda `Telefondan (aynı Wi-Fi): http://192.168.x.x:5000` gibi bir adres yazar.

2. Uygulamaya bu adresi ver ve Android projesine aktar (bu klasörde):

   ```bash
   npm install
   npm run adres -- http://192.168.x.x:5000
   npm run esitle
   ```

   Android emülatöründe denerken adres `http://10.0.2.2:5000` olabilir (emülatör bilgisayarı bu adresle görür). Varsayılan budur.

3. Android Studio'da aç ve çalıştır:

   ```bash
   npm run android
   ```

   Android Studio'da ▶ ile telefona ya da emülatöre kurulur. APK dosyası için **Build › Build App Bundle(s) / APK(s) › Build APK(s)**;
   dosya `android/app/build/outputs/apk/debug/app-debug.apk` olarak çıkar. Bu dosyayı telefona atıp kurabilirsin.

## Anlık bildirim (isteğe bağlı)

Uygulama kapalıyken de bildirim gelmesi için Firebase Cloud Messaging kullanılır. Ücretsizdir ama bir kez ayarlamak gerekir:

1. [Firebase konsolunda](https://console.firebase.google.com) bir proje aç ve **Android uygulaması ekle** de.
   Paket adı: `com.agora.forum`.
2. İndirilen `google-services.json` dosyasını `mobil/android/app/` klasörüne koy.
3. Firebase konsolunda **Proje ayarları › Hizmet hesapları › Yeni özel anahtar oluştur** ile bir JSON dosyası indir,
   adını `firebase.json` yapıp sunucudaki `instance/` klasörüne koy. Bu dosya gizlidir; kimseyle paylaşma.
4. Sunucuda `pip install pywebpush` çalıştır (imza için gereken kütüphaneyi de kurar), sunucuyu yeniden başlat.
5. Bu klasörde `npm run esitle`, sonra Android Studio'da uygulamayı yeniden derle.

Sonra uygulamada **Panelim › Bildirimler › Bu cihazda aç**. Bildirime dokununca ilgili sayfa açılır.
Tarayıcıdaki anlık bildirim için Firebase gerekmez; yalnızca `pip install pywebpush` yeter (site HTTPS adreste olmalı).

## Kalıcı bir sunucuya taşıyınca

Forum internette bir alan adında (ör. `https://agora.ornek.com`) yayınlanırsa `npm run adres -- https://agora.ornek.com`
ve `npm run esitle` yeter. HTTPS adreslerde şifresiz bağlantı izni kendiliğinden kapanır.

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
