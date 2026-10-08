"""S02-50 mini laboratuvar, 1. görev: 10 Türkçe cümle ve İngilizce çevirileri tiktoken ile tokenlara ayrılır; ortalama
token oranı (Türkçe / İngilizce) raporlanır.

    python laboratuvar/token_orani.py

İki kodlayıcı ölçülür: cl100k_base (GPT-4, GPT-3.5) ve o200k_base (GPT-4o ve sonrası). tiktoken kodlayıcı dosyasını ilk
çalıştırmada indirir ve SHA-256 özetini denetler. Ders slaytı (S02-4…6): Türkçe gibi az temsil edilen ve sondan eklemeli
dillerde aynı anlam daha çok tokenla yazılır; bu da gecikme, maliyet ve bağlam penceresi demektir.
"""
import statistics

import tiktoken

# Cümleler forumun kendi konularından seçildi; son cümle sondan eklemeliliğin uç örneğidir.
CUMLELER = [
    ("Yemekhanede haftada bir gün etsiz menü olsun.",
     "There should be a meat-free menu one day a week in the cafeteria."),
    ("Kütüphanenin çalışma saatleri sınav haftasında uzatılmalı.",
     "The library's opening hours should be extended during exam week."),
    ("Kampüs içi ring otobüsleri gece de çalışsın.",
     "Campus shuttle buses should also run at night."),
    ("Öğrenci kulüplerine ayrılan bütçe artırılmalıdır.",
     "The budget allocated to student clubs should be increased."),
    ("Bu konudaki oylamaya katılamayanlar itiraz edebilir.",
     "Those who could not take part in the vote on this topic may object."),
    ("Fikirler tur tur oylanarak karara bağlanır.",
     "Ideas are decided by voting on them round by round."),
    ("Kişisel verilerinizi forumda paylaşmayın.",
     "Do not share your personal data on the forum."),
    ("Uzmanların oyu daha ağır sayılır ama kalabalığı tek başına yenemez.",
     "Experts' votes count more, but they cannot outvote the crowd on their own."),
    ("Kayıt defteri, oyların sonradan değiştirilmediğini gösterir.",
     "The ledger shows that the votes were not changed afterwards."),
    ("Avrupalılaştıramadıklarımızdan mısınız?",
     "Are you one of those whom we could not Europeanize?"),
]
KODLAYICILAR = ("cl100k_base", "o200k_base")


def olc():
    """Döner: {kodlayıcı: [(tr_token, en_token), ...]}"""
    sonuc = {}
    for ad in KODLAYICILAR:
        k = tiktoken.get_encoding(ad)
        sonuc[ad] = [(len(k.encode(tr)), len(k.encode(en))) for tr, en in CUMLELER]
    return sonuc


def parcalar(ad, metin):
    k = tiktoken.get_encoding(ad)
    return [k.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in k.encode(metin)]


def main():
    sonuc = olc()
    print("| # | Türkçe cümle | Kelime TR / EN | " + " | ".join(f"{ad} TR / EN (oran)" for ad in KODLAYICILAR) + " |")
    print("|---|---|---|" + "---|" * len(KODLAYICILAR))
    for i, (tr, en) in enumerate(CUMLELER):
        hucreler = [f"{sonuc[ad][i][0]} / {sonuc[ad][i][1]} ({sonuc[ad][i][0] / sonuc[ad][i][1]:.2f})"
                    for ad in KODLAYICILAR]
        print(f"| {i + 1} | {tr} | {len(tr.split())} / {len(en.split())} | " + " | ".join(hucreler) + " |")
    print()
    for ad in KODLAYICILAR:
        oranlar = [t / e for t, e in sonuc[ad]]
        toplam_tr, toplam_en = sum(t for t, _ in sonuc[ad]), sum(e for _, e in sonuc[ad])
        karakter = sum(len(tr) for tr, _ in CUMLELER) / toplam_tr
        print(f"{ad}: ortalama oran {statistics.mean(oranlar):.2f} (en düşük {min(oranlar):.2f}, en yüksek "
              f"{max(oranlar):.2f}); toplam {toplam_tr} / {toplam_en} = {toplam_tr / toplam_en:.2f}; "
              f"Türkçede token başına {karakter:.1f} karakter")
    print()
    for ad in KODLAYICILAR:
        print(f"{ad}: 'Avrupalılaştıramadıklarımızdan' → {parcalar(ad, 'Avrupalılaştıramadıklarımızdan')}")


if __name__ == "__main__":
    main()
