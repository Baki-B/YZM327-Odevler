// Agora mobil uygulaması (Expo Go ile açılır).
// Uygulama, Agora sunucusundaki siteyi tam ekran bir WebView içinde açar: sayfalar, hesap ve veritabanı web sitesiyle aynıdır.
// Uygulamaya özgü olanlar: sunucu adresi ekranı, Android geri tuşu, çentik boşlukları, durum çubuğu rengi,
// site dışı bağlantıların tarayıcıda açılması ve bağlantı hatası ekranı.
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator, BackHandler, Image, KeyboardAvoidingView, Linking, Platform, Pressable, StyleSheet, Text, TextInput,
  View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';

const RENK = { tas: '#ebe7df', kart: '#f6f4ef', cizgi: '#dfd9ce', yazi: '#2c2a27', soluk: '#6f6a62', yesil: '#4a6642' };
const ADRES_ANAHTARI = 'agora-sunucu';
const ADRES_SAYFASI = '/uygulama/adres';   // sitedeki "Sunucu adresini değiştir" bağlantısı bu ekranı açar
const FORUM_PORTU = 5000;

// Expo Go projeyi bilgisayardan yüklediği için bilgisayarın ağdaki adresini biliyoruz; forum da çoğunlukla oradadır.
function tahminiAdres() {
  const kaynak = Constants.expoConfig?.hostUri || Constants.expoGoConfig?.debuggerHost || '';
  const makine = kaynak.split(':')[0];
  return makine ? `http://${makine}:${FORUM_PORTU}` : '';
}

function adresiDuzelt(metin) {
  let a = (metin || '').trim().replace(/\/+$/, '');
  if (a && !/^https?:\/\//i.test(a)) a = `http://${a}`;
  return a;
}

async function sunucuyuDene(adres) {
  const denetci = new AbortController();
  const zamanlayici = setTimeout(() => denetci.abort(), 6000);
  try {
    const y = await fetch(`${adres}/api/v1`, { signal: denetci.signal });
    const v = await y.json();
    return Boolean(v && v.ad);
  } catch {
    return false;
  } finally {
    clearTimeout(zamanlayici);
  }
}

export default function App() {
  return (
    <SafeAreaProvider>
      <Kok />
    </SafeAreaProvider>
  );
}

function Kok() {
  const [adres, setAdres] = useState(null);       // null: henüz okunmadı, '': ayarlanmamış
  const [adresEkrani, setAdresEkrani] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(ADRES_ANAHTARI).then((kayitli) => setAdres(kayitli || ''));
  }, []);

  if (adres === null) {
    return <View style={[stil.ortala, { backgroundColor: RENK.tas }]}><ActivityIndicator color={RENK.yesil} /></View>;
  }
  if (!adres || adresEkrani) {
    return (
      <AdresEkrani
        mevcut={adres || tahminiAdres()}
        vazgecilebilir={Boolean(adres)}
        onVazgec={() => setAdresEkrani(false)}
        onKaydet={async (yeni) => {
          await AsyncStorage.setItem(ADRES_ANAHTARI, yeni);
          setAdres(yeni);
          setAdresEkrani(false);
        }}
      />
    );
  }
  return <Forum adres={adres} onAdresDegistir={() => setAdresEkrani(true)} />;
}

// --- Sunucu adresi ---

function AdresEkrani({ mevcut, vazgecilebilir, onVazgec, onKaydet }) {
  const [metin, setMetin] = useState(mevcut);
  const [durum, setDurum] = useState('');
  const [bekliyor, setBekliyor] = useState(false);

  const baglan = async () => {
    const adres = adresiDuzelt(metin);
    if (!adres) { setDurum('Sunucu adresini yaz.'); return; }
    setBekliyor(true);
    setDurum('');
    const tamam = await sunucuyuDene(adres);
    setBekliyor(false);
    if (tamam) onKaydet(adres);
    else setDurum(`${adres} adresinde Agora bulunamadı. Sunucunun “python calistir.py --ag” ile açık olduğundan ve telefonun aynı Wi-Fi ağında olduğundan emin ol.`);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: RENK.tas }}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={stil.ortala} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={stil.kart}>
          <Image source={require('./assets/icon.png')} style={stil.logo} />
          <Text style={stil.baslik}>{'Agora’ya bağlan'}</Text>
          <Text style={stil.aciklama}>
            {'Forumun çalıştığı sunucunun adresini yaz. Bilgisayarında “python calistir.py --ag” komutunun ekrana ' +
              'yazdığı “Telefondan” adresini kullanabilirsin.'}
          </Text>
          <TextInput
            style={stil.girdi}
            value={metin}
            onChangeText={setMetin}
            placeholder="http://192.168.1.20:5000"
            placeholderTextColor={RENK.soluk}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            returnKeyType="go"
            onSubmitEditing={baglan}
          />
          {durum ? <Text style={stil.hata}>{durum}</Text> : null}
          <Pressable style={({ pressed }) => [stil.dugme, pressed && { opacity: 0.85 }]} onPress={baglan} disabled={bekliyor}>
            {bekliyor ? <ActivityIndicator color={RENK.kart} /> : <Text style={stil.dugmeYazi}>Bağlan</Text>}
          </Pressable>
          {vazgecilebilir ? (
            <Pressable style={stil.ikinciDugme} onPress={onVazgec}><Text style={stil.ikinciYazi}>Vazgeç</Text></Pressable>
          ) : null}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// --- Forum ---

// Sayfa açılırken çalışır: çentik boşluklarını CSS değişkeni olarak verir (style.css bunları kullanır) ve sayfanın
// açık/koyu olduğunu uygulamaya bildirir; durum çubuğunun yazı rengi buna göre değişir.
function sayfaBetigi(kenar) {
  return `(function () {
    var k = ${JSON.stringify(kenar)};
    function uygula() {
      var s = document.documentElement.style;
      s.setProperty('--safe-area-inset-top', k.top + 'px');
      s.setProperty('--safe-area-inset-bottom', k.bottom + 'px');
      s.setProperty('--safe-area-inset-left', k.left + 'px');
      s.setProperty('--safe-area-inset-right', k.right + 'px');
    }
    function temaBildir() {
      if (!document.body || !window.ReactNativeWebView) return;
      var r = getComputedStyle(document.body).backgroundColor.match(/\\d+/g) || [255, 255, 255];
      var parlaklik = (0.299 * r[0] + 0.587 * r[1] + 0.114 * r[2]) / 255;
      window.ReactNativeWebView.postMessage(JSON.stringify({ koyu: parlaklik < 0.5, zemin: getComputedStyle(document.body).backgroundColor }));
    }
    uygula();
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { uygula(); temaBildir(); });
    else temaBildir();
    new MutationObserver(function () { setTimeout(temaBildir, 30); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ['data-tema'] });
    if (window.matchMedia) {
      var m = window.matchMedia('(prefers-color-scheme: dark)');
      if (m.addEventListener) m.addEventListener('change', function () { setTimeout(temaBildir, 30); });
    }
  })(); true;`;
}

function Forum({ adres, onAdresDegistir }) {
  const kenar = useSafeAreaInsets();
  const web = useRef(null);
  const [geriGidebilir, setGeriGidebilir] = useState(false);
  const [hata, setHata] = useState(false);
  const [koyu, setKoyu] = useState(false);
  const [zemin, setZemin] = useState(RENK.tas);
  const [anahtar, setAnahtar] = useState(0);        // "Tekrar dene" WebView'i baştan kurar
  const kok = adres.replace(/\/+$/, '');
  const betik = sayfaBetigi({ top: kenar.top, bottom: kenar.bottom, left: kenar.left, right: kenar.right });

  // Android geri tuşu: önce sayfa geçmişinde geri, geçmiş bitince uygulamadan çık
  useEffect(() => {
    if (Platform.OS !== 'android') return undefined;
    const abonelik = BackHandler.addEventListener('hardwareBackPress', () => {
      if (geriGidebilir && web.current) { web.current.goBack(); return true; }
      return false;
    });
    return () => abonelik.remove();
  }, [geriGidebilir]);

  // Site içi bağlantılar uygulamada, site dışı bağlantılar telefonun tarayıcısında açılır
  const istekDenetle = useCallback((istek) => {
    const url = istek.url || '';
    if (url.startsWith(kok + ADRES_SAYFASI)) { onAdresDegistir(); return false; }
    if (url.startsWith(kok) || url.startsWith('about:') || url.startsWith('data:') || url.startsWith('blob:')) return true;
    if (/^https?:/i.test(url) || /^(mailto|tel):/i.test(url)) { Linking.openURL(url).catch(() => {}); return false; }
    return false;
  }, [kok, onAdresDegistir]);

  const mesaj = useCallback((olay) => {
    try {
      const v = JSON.parse(olay.nativeEvent.data);
      if (typeof v.koyu === 'boolean') setKoyu(v.koyu);
      if (typeof v.zemin === 'string') setZemin(v.zemin);
    } catch { /* sayfadan beklenmeyen mesaj */ }
  }, []);

  if (hata) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: RENK.tas }}>
        <StatusBar style="dark" />
        <View style={stil.ortala}>
          <View style={stil.kart}>
            <Image source={require('./assets/icon.png')} style={stil.logo} />
            <Text style={stil.baslik}>Sunucuya bağlanılamadı</Text>
            <Text style={stil.aciklama}>
              {kok} adresine ulaşılamıyor. Sunucunun açık olduğundan ve telefonun aynı Wi-Fi ağında olduğundan emin ol.
            </Text>
            <Pressable style={stil.dugme} onPress={() => { setHata(false); setAnahtar((n) => n + 1); }}>
              <Text style={stil.dugmeYazi}>Tekrar dene</Text>
            </Pressable>
            <Pressable style={stil.ikinciDugme} onPress={onAdresDegistir}>
              <Text style={stil.ikinciYazi}>Sunucu adresini değiştir</Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: zemin }}>
      <StatusBar style={koyu ? 'light' : 'dark'} />
      <WebView
        key={anahtar}
        ref={web}
        source={{ uri: kok + '/' }}
        style={{ flex: 1, backgroundColor: zemin }}
        applicationNameForUserAgent="AgoraMobil"
        injectedJavaScriptBeforeContentLoaded={betik}
        injectedJavaScript={betik}
        onMessage={mesaj}
        onNavigationStateChange={(d) => setGeriGidebilir(d.canGoBack)}
        onShouldStartLoadWithRequest={istekDenetle}
        onError={() => setHata(true)}
        onRenderProcessGone={() => setAnahtar((n) => n + 1)}
        onContentProcessDidTerminate={() => web.current && web.current.reload()}
        startInLoadingState
        renderLoading={() => (
          <View style={[StyleSheet.absoluteFill, stil.ortala, { backgroundColor: RENK.tas }]}>
            <ActivityIndicator color={RENK.yesil} size="large" />
          </View>
        )}
        setSupportMultipleWindows={false}
        allowsBackForwardNavigationGestures
        pullToRefreshEnabled
        overScrollMode="never"
        domStorageEnabled
        javaScriptEnabled
        sharedCookiesEnabled
        thirdPartyCookiesEnabled={false}
        mixedContentMode="never"
        textZoom={100}
      />
    </View>
  );
}

const stil = StyleSheet.create({
  ortala: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 20 },
  kart: {
    width: '100%', maxWidth: 420, backgroundColor: RENK.kart, borderRadius: 20, padding: 24, borderWidth: 1,
    borderColor: RENK.cizgi, alignItems: 'stretch',
  },
  logo: { width: 72, height: 72, borderRadius: 18, alignSelf: 'center', marginBottom: 14 },
  baslik: { fontSize: 22, fontWeight: '800', color: RENK.yazi, textAlign: 'center', marginBottom: 8 },
  aciklama: { fontSize: 15, lineHeight: 22, color: RENK.soluk, textAlign: 'center', marginBottom: 18 },
  girdi: {
    borderWidth: 1.5, borderColor: RENK.cizgi, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16,
    color: RENK.yazi, backgroundColor: '#fff', marginBottom: 12,
  },
  hata: { color: RENK.yazi, fontWeight: '600', marginBottom: 12, lineHeight: 20 },
  dugme: { backgroundColor: RENK.yesil, borderRadius: 12, paddingVertical: 14, alignItems: 'center' },
  dugmeYazi: { color: RENK.kart, fontWeight: '800', fontSize: 16 },
  ikinciDugme: { paddingVertical: 12, alignItems: 'center', marginTop: 6 },
  ikinciYazi: { color: RENK.yesil, fontWeight: '700', fontSize: 15 },
});
