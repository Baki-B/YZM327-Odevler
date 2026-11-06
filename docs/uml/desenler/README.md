# Tasarım desenleri ve SOLID ilkeleri

Hepsi tek dosyada: **[Agora_Desenler_ve_SOLID.pdf](Agora_Desenler_ve_SOLID.pdf)**. Kaynaklar PlantUML (`*.puml`).

Agora'daki dokuz tasarım deseni (sekizi GoF, biri Repository) ve beş SOLID ilkesi üç sınıf diyagramında. Sınıfların üstündeki «Strategy», «Handler» gibi
etiketler sınıfın desendeki rolünü, yeşil notlar o yerde uygulanan SOLID ilkesini gösteriyor.

| Diyagram | Desenler | SOLID |
|---|---|---|
| [1. Oylama türleri ve konu durumları](svg/1_oylama_ve_konu_durumlari.svg) | Strategy, Template Method, State | S, O, L |
| [2. Denetim, bildirim ve konu sayfası](svg/2_denetim_bildirim_konu_sayfasi.svg) | Chain of Responsibility, Adapter, Facade | S, O, L, I |
| [3. Kayıt defteri](svg/3_kayit_defteri.svg) | Observer, Memento, Repository | S, L, I, D |

Her desenin önceki sorunu ve testi: [docs/tasarim.md](../../tasarim.md) 8. bölüm.

Yeniden üretmek (bu klasörde): `java -jar plantuml.jar -charset UTF-8 -tsvg -o svg *.puml`, ardından
`node docs/uml/desenler/pdf_uret.mjs`.
