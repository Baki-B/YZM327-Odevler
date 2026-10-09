# UML diyagramları

Hepsi tek dosyada: **[Agora_UML_Diyagramlari.pdf](Agora_UML_Diyagramlari.pdf)**. Kaynaklar PlantUML (`*.puml`), çizimler `svg/` ve `png/` klasörlerinde.
Sınıf ve işlev adları kaynak koddakilerle aynıdır. Durum diyagramı ve varlık–ilişki diyagramı [tasarim.md](../tasarim.md)'de.

## Kullanım durumu diyagramları
| Diyagram | İçerik |
|---|---|
| [Ziyaretçi, üye, uzman](svg/01a_kullanim_durumlari_uye.svg) | Okuma, kayıt, konu açma, mesaj ve fikir, oy verme, makbuz, devir, şikayet, başvurular; `include`/`extend` ilişkileri |
| [Yönetici ve otomatik işler](svg/01b_kullanim_durumlari_yonetim.svg) | Ayrı yönetici girişi, panel işlemleri; zamanlayıcı ve yapay zeka üye |

## Sınıf diyagramları
| Diyagram | İçerik |
|---|---|
| [Alan modeli](svg/02a_sinif_alan_modeli.svg) | Kullanıcı, konu, mesaj, teklif, seçenek, oy, karar ve diğer varlıklar; nitelikler ve çokluklar |
| [Konu durumları ve oylama türleri](svg/02b_sinif_konu_ve_oylama.svg) | State; Strategy + Template Method + Registry |
| [Denetim ve konu sayfası](svg/02c_sinif_denetim_ve_konu_sayfasi.svg) | Chain of Responsibility (D1–D7); Facade |
| [Kayıt defteri ve anlık bildirim](svg/02d_sinif_defter_ve_bildirim.svg) | Observer + Repository; Adapter |

## Sıralı diyagramlar
| Diyagram | Akış |
|---|---|
| [Kayıt olma](svg/03a_sirali_kayit.svg) | Doğrulama, şifre ve kurtarma kodu özeti, oturum |
| [Konu açma](svg/03b_sirali_konu_acma.svg) | Yönetmelik denetimi zinciri, engel / uyarı |
| [Oy verme ve makbuz](svg/03c_sirali_oy_verme.svg) | Oy ağırlığı, koşullu yazma, taahhüt, defter, makbuzla doğrulama |
| [Tur sonu](svg/03d_sirali_tur_sonu.svg) | Şablon yöntem, tur kararı, kayıt noktası ile hata yalıtımı |
| [Şikayetten gizleme oylamasına](svg/03e_sirali_sikayet_gizleme.svg) | Şikayet tabanı, yöneticinin oylamaya alması, 3/4 karar |
| [Yönetici girişi ve askıya alma](svg/03f_sirali_yonetici.svg) | Ayrı yönetici oturumu, askı, günlük ve defter |
| [Tarayıcı sürümünde bir istek](svg/03g_sirali_tarayici_surumu.svg) | Service worker → kabuk → Pyodide'deki Flask → IndexedDB |

Yeniden üretmek: `java -jar plantuml.jar -charset UTF-8 -tsvg -o svg 0*.puml`, ardından `node docs/uml/pdf_uret.mjs`.
