# UML diyagramları

Hepsi tek dosyada: **[Agora_UML_Diyagramlari.pdf](Agora_UML_Diyagramlari.pdf)**. Kaynaklar PlantUML (`*.puml`).

| Diyagram | Gösterdiği |
|---|---|
| [Kullanım durumu](svg/1_kullanim_durumu.svg) | Kim sistemle ne yapabiliyor |
| [Sınıf](svg/2_sinif.svg) | Kullanıcı, konu, mesaj, oylama, seçenek, oy, karar, kategori ve ilişkileri |
| [Sıralı: konu açma](svg/3a_sirali_konu_acma.svg) | Konu kaydedilmeden önce yönetmelik denetimi |
| [Sıralı: oy verme](svg/3b_sirali_oy_verme.svg) | Oy, kayıt defteri ve makbuz |
| [Sıralı: tur sonu](svg/3c_sirali_tur_sonu.svg) | Oyların sayılması; karar ya da sonraki tur |

Ayrıntılı hâlleri (tasarım desenlerinin sınıf diyagramları, yedi sıralı diyagram): [ayrintili/](ayrintili/).

Yeniden üretmek: `java -jar plantuml.jar -charset UTF-8 -tsvg -o svg [123]*.puml`, ardından `node docs/uml/pdf_uret.mjs`.
