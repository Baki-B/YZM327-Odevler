"""S02-50 mini laboratuvar, 2. görev: slayttaki NumPy dikkat kodu (S02-13) 5 tokenlık bir cümleye genişletilir, nedensel
maske eklenir ve ağırlık matrisi ısı haritası olarak çizilir.

    python laboratuvar/dikkat.py        # sonuçları yazar, laboratuvar/dikkat_isi_haritasi.png dosyasını üretir

Nedensel maske (S02-11): otoregresif modelde bir token yalnızca kendisine ve öncekilere bakar; sonraki tokenların puanı
softmax'tan önce −∞ yapılır, böylece ağırlıkları tam 0 olur.
"""
import os

import numpy as np

KLASOR = os.path.dirname(os.path.abspath(__file__))


def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))      # taşmayı önleyen kararlılık hilesi; sonucu değiştirmez
    return e / e.sum(axis=-1, keepdims=True)


def dikkat(Q, K, V, nedensel=False):
    """Ölçeklenmiş nokta çarpımı dikkati. nedensel=True: i. sorgu j > i anahtarlarını göremez."""
    d = Q.shape[-1]
    puan = Q @ K.T / np.sqrt(d)                          # (sorgu, anahtar)
    if nedensel:
        puan = np.where(np.triu(np.ones_like(puan, dtype=bool), k=1), -np.inf, puan)
    w = softmax(puan)                                    # her satırın toplamı 1
    return w @ V, w


def slayt_ornegi():
    """S02-12/13'teki "Kedi süt içti" örneği: aynı sonuç çıkmalı (kodun doğru genişletildiğinin kanıtı)."""
    K = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0]], float)
    V = np.array([[1, 0], [0, 1], [0.5, 0.5]])
    Q = np.array([[1, 0, 1, 0]], float)                  # "içti"
    cikti, w = dikkat(Q, K, V)
    assert np.allclose(w.round(3), [[0.506, 0.186, 0.307]]) and np.allclose(cikti.round(3), [[0.66, 0.34]])
    return w, cikti


# 5 tokenlık cümle. Vektörler öğretim amaçlı seçildi (gerçek modellerde yüzlerce boyut ve öğrenilmiş ağırlıklar vardır).
# Boyutlar kabaca: [canlı/özne, nesne/sıvı, eylem, yer/zaman]
TOKENLAR = ["Kedi", "bahçede", "süt", "içip", "uyudu"]
X = np.array([
    [1.0, 0.0, 0.2, 0.0],    # Kedi
    [0.0, 0.1, 0.0, 1.0],    # bahçede
    [0.0, 1.0, 0.1, 0.0],    # süt
    [0.6, 0.8, 1.0, 0.0],    # içip   (kim içti? ne içti?)
    [0.9, 0.0, 1.0, 0.3],    # uyudu  (kim uyudu?)
])
V5 = np.array([[1, 0], [0, 0], [0, 1], [0.5, 0.5], [0.5, 0.5]], float)   # 2 boyutlu değer: [özne bilgisi, nesne bilgisi]


def bes_token():
    """Öz-dikkat (Q = K = X): maskesiz ve nedensel maskeli ağırlıklar."""
    _, w_acik = dikkat(X, X, V5)
    cikti, w_maskeli = dikkat(X, X, V5, nedensel=True)
    return w_acik, w_maskeli, cikti


def ciz(w_acik, w_maskeli, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    # Tek renk tonu, açıktan koyuya (büyüklük); uygulamanın yeşili. Maskelenen hücreler nötr gri ve tarama ile.
    ton = LinearSegmentedColormap.from_list("agora", ["#f3f1ea", "#b9c9ae", "#4a6642", "#24361f"])
    murekkep, soluk = "#2c2a27", "#6d6961"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, eksenler = plt.subplots(1, 2, figsize=(8.6, 3.7), dpi=200, constrained_layout=True)
    for eksen, w, baslik in ((eksenler[0], w_acik, "Maskesiz (çift yönlü)"),
                             (eksenler[1], w_maskeli, "Nedensel maske (yalnızca öncekiler)")):
        maske = np.triu(np.ones_like(w, dtype=bool), k=1) if w is w_maskeli else np.zeros_like(w, dtype=bool)
        goster = np.ma.masked_where(maske, w)
        eksen.set_facecolor("#e4e1d9")
        resim = eksen.imshow(goster, cmap=ton, vmin=0, vmax=1)
        for i in range(w.shape[0]):
            for j in range(w.shape[1]):
                if maske[i, j]:
                    eksen.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="///",
                                                  edgecolor="#c9c4b8", linewidth=0))
                    eksen.text(j, i, "0", ha="center", va="center", color=soluk, fontsize=8)
                else:
                    eksen.text(j, i, f"{w[i, j]:.2f}".replace(".", ","), ha="center", va="center", fontsize=8,
                               color="#ffffff" if w[i, j] > 0.55 else murekkep)
        eksen.set_xticks(range(len(TOKENLAR)), TOKENLAR, color=murekkep)
        eksen.set_yticks(range(len(TOKENLAR)), TOKENLAR, color=murekkep)
        eksen.set_xlabel("anahtar (bakılan token)", color=soluk)
        eksen.set_ylabel("sorgu (bakan token)", color=soluk)
        eksen.set_title(baslik, color=murekkep, fontsize=10)
        eksen.tick_params(length=0)
        for kenar in eksen.spines.values():
            kenar.set_visible(False)
        # Hücreler arasında 2 piksellik yüzey boşluğu
        eksen.set_xticks(np.arange(-0.5, 5, 1), minor=True)
        eksen.set_yticks(np.arange(-0.5, 5, 1), minor=True)
        eksen.grid(which="minor", color="#ffffff", linewidth=2)
        eksen.tick_params(which="minor", length=0)
    renk = fig.colorbar(resim, ax=eksenler, shrink=0.85, pad=0.02)
    renk.set_label("dikkat ağırlığı (satır toplamı = 1)", color=soluk)
    renk.outline.set_visible(False)
    fig.savefig(yol, facecolor="#ffffff")
    plt.close(fig)


def main():
    w, cikti = slayt_ornegi()
    print(f"Slayt örneği (Kedi süt içti, sorgu 'içti'): ağırlık {w.round(3).tolist()}, çıktı {cikti.round(3).tolist()} ✓")
    w_acik, w_maskeli, cikti = bes_token()
    np.set_printoptions(precision=3, suppress=True)
    print("\n5 token:", " ".join(TOKENLAR))
    print("\nMaskesiz ağırlıklar (satır = sorgu):\n", w_acik)
    print("\nNedensel maskeli ağırlıklar:\n", w_maskeli)
    assert np.allclose(w_maskeli.sum(axis=1), 1) and np.all(w_maskeli[np.triu_indices(5, k=1)] == 0)
    print("\nDenetim: her satırın toplamı 1, köşegenin üstü tam 0 ✓")
    print("Maskeli çıktı (her tokenın yeni temsili, [özne, nesne]):\n", cikti)
    yol = os.path.join(KLASOR, "dikkat_isi_haritasi.png")
    ciz(w_acik, w_maskeli, yol)
    print(f"\nIsı haritası: {os.path.relpath(yol)}")


if __name__ == "__main__":
    main()
