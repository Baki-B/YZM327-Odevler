# UML diyagramları

Hepsi tek dosyada: **[Agora_UML_Diyagramlari.pdf](Agora_UML_Diyagramlari.pdf)**. Kaynaklar PlantUML (`*.puml`).

| Diyagram | Gösterdiği |
|---|---|
| [Kullanım durumu](svg/1_kullanim_durumu.svg) | 3 aktör (ziyaretçi, üye, yönetici) ve 5 kullanım durumu |
| [Sınıf](svg/2_sinif.svg) | Kullanıcı, konu, mesaj, oylama, fikir, oy ve ilişkileri |
| [Sıralı: konu açma](svg/3a_sirali_konu_acma.svg) | Üye → sistem → veritabanı |
| [Sıralı: oy verme](svg/3b_sirali_oy_verme.svg) | Oy hakkı kontrolü, kayıt, makbuz |
| [Sıralı: tur sonu](svg/3c_sirali_tur_sonu.svg) | Oyların sayılması ve eleme |

Ayrıntılı hâlleri (tasarım desenlerinin sınıf diyagramları, yedi sıralı diyagram): [ayrintili/](ayrintili/).

Yeniden üretmek: `java -jar plantuml.jar -charset UTF-8 -tsvg -o svg [123]*.puml`, ardından `node docs/uml/pdf_uret.mjs`.
