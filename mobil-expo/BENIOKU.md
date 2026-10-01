# Agora — Expo Go uygulaması

Bu klasör Agora'nın **Expo Go** ile açılan mobil uygulamasıdır (Expo SDK 57; Expo Go 57.x ile uyumlu).
Uygulama, Agora sunucusundaki siteyi tam ekran açar. Bu yüzden web sitesiyle aynı sayfaları, aynı hesabı ve aynı
veritabanını kullanır; sitede yapılan her değişiklik uygulamaya da yansır.

Uygulamaya özel olanlar:

- İlk açılışta **sunucu adresi ekranı**. Adres, Expo'nun çalıştığı bilgisayardan tahmin edilir (`http://BILGISAYAR-IP:5000`);
  gerekirse değiştirilir ve telefonda saklanır. Daha sonra **Panelim › Uygulama ve API › Sunucu adresini değiştir** ile değişir.
- Android geri tuşu önce sayfa geçmişinde geri gider, geçmiş bitince uygulamadan çıkar. iPhone'da kaydırarak geri gidilir.
- Çentik ve sistem çubuğu boşlukları sayfaya verilir; durum çubuğu açık ve koyu temaya göre renk değiştirir.
- Site dışı bağlantılar telefonun tarayıcısında açılır.
- Sunucuya ulaşılamazsa “Sunucuya bağlanılamadı” ekranı çıkar (Tekrar dene / Sunucu adresini değiştir).
- Telefonda sitenin alt sekme çubuğu görünür (Konular, Oylamalar, yeni konu, Meclis, Panelim).

## Çalıştırma

1. Telefona **Expo Go** uygulamasını kur (Google Play ya da App Store).
2. Bilgisayarda forumu ağa açık başlat (proje klasöründe):

   ```bash
   python calistir.py --ag
   ```

3. Başka bir terminalde bu klasörde Expo'yu başlat:

   ```bash
   npm install
   npx expo start
   ```

4. Ekranda çıkan QR kodu Android'de Expo Go ile, iPhone'da kamerayla okut.
5. Uygulama açılınca sunucu adresini onayla. `calistir.py` ekrana `Telefondan (aynı Wi-Fi): http://192.168.x.x:5000`
   gibi bir adres yazar; uygulamadaki adres bununla aynı olmalı.

Telefon ve bilgisayar **aynı Wi-Fi ağında** olmalı. Windows ilk çalıştırmada Python ve Node için güvenlik duvarı izni sorar;
“Özel ağlar” için izin ver. Okul/iş ağları cihazların birbirini görmesini engelleyebilir; o zaman `npx expo start --tunnel`
ile Expo açılır, ama forumun kendisi yine aynı ağdan erişilebilir olmalı (ya da internette yayınlanmalı).

## Expo Go'nun sınırı: anlık bildirim

Expo Go, uygulama kapalıyken gelen anlık bildirimleri (push) desteklemez. Site içindeki bildirimler (zil simgesi)
normal çalışır. Telefona anlık bildirim için ya `mobil/` klasöründeki Android uygulamasını (Capacitor + Firebase)
ya da bir Expo geliştirme derlemesini (`npx eas-cli@latest build --profile development`) kullanmak gerekir.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `App.js` | Uygulamanın tamamı: sunucu adresi ekranı, WebView, geri tuşu, çentik boşlukları, hata ekranı |
| `app.json` | Ad (Agora), simge, paket kimliği (`com.agora.forum`), açık/koyu tema |
| `assets/` | Forumun simgesinden üretilen uygulama simgeleri |
