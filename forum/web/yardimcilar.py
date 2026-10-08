"""Şablon yardımcıları: güvenli metin biçimlendirme, avatar, sayfalama."""
import hashlib
import math
import re
from base64 import b64encode

from markupsafe import Markup, escape

from ..ayarlar import GRI, TAS_BEYAZI, YESIL

_URL = re.compile(r"(https?://[^\s<]+)")
_BAHSETME = re.compile(r"(?<![\w/])@([A-Za-z0-9_.çğıöşüÇĞİÖŞÜ]{3,30})")
_KALIN = re.compile(r"\*\*(.+?)\*\*")


def bicimle(metin, kok=""):
    """Önce HTML kaçışı, sonra güvenli biçimler: bağlantı, @bahsetme, **kalın**. Satır sonları CSS ile korunur.
    `kok`, uygulama bir alt yolda çalışıyorsa (GitHub Pages) bahsetme bağlantılarının önüne eklenir."""
    if not metin:
        return ""
    e = str(escape(metin))
    parcalar = _URL.split(e)
    for i, p in enumerate(parcalar):
        if i % 2:   # URL
            parcalar[i] = f'<a href="{p}" rel="nofollow noopener noreferrer" target="_blank">{p}</a>'
        else:
            p = _BAHSETME.sub(rf'<a class="bahsetme" href="{kok}/kullanici/\1">@\1</a>', p)
            parcalar[i] = _KALIN.sub(r"<strong>\1</strong>", p)
    return Markup("".join(parcalar))


# Avatar zemin/desen çiftleri: sadece paletteki renkler (taş beyazı, yeşil, gri)
AVATAR_CIFTLERI = [(YESIL[200], YESIL[700]), (TAS_BEYAZI[200], GRI[700]), (YESIL[600], TAS_BEYAZI[50]),
                   (GRI[300], YESIL[800]), (YESIL[100], YESIL[600]), (YESIL[800], YESIL[200])]


def avatar(takma_ad, yz_mi=False):
    """Takma addan türetilen simetrik desen (identicon) — veri URI'si olarak SVG."""
    h = hashlib.sha256((takma_ad or "?").encode()).digest()
    if yz_mi:
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" rx="2" '
               f'fill="{YESIL[700]}"/><text x="5" y="6.8" font-size="4.2" text-anchor="middle" fill="{TAS_BEYAZI[50]}" '
               'font-family="sans-serif" font-weight="bold">YZ</text></svg>')
    else:
        zemin, renk = AVATAR_CIFTLERI[h[0] % len(AVATAR_CIFTLERI)]
        kareler = []
        for y in range(5):
            for x in range(3):
                if h[1 + y * 3 + x] % 2:
                    for xx in {x, 4 - x}:
                        kareler.append(f'<rect x="{xx * 2}" y="{y * 2}" width="2" height="2" fill="{renk}"/>')
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" rx="2" '
               f'fill="{zemin}"/>{"".join(kareler)}</svg>')
    return "data:image/svg+xml;base64," + b64encode(svg.encode()).decode()


def sayfala(liste, sayfa, boy):
    toplam = len(liste)
    sayfa_sayisi = max(1, math.ceil(toplam / boy))
    sayfa = min(max(1, sayfa), sayfa_sayisi)
    return liste[(sayfa - 1) * boy: sayfa * boy], {"sayfa": sayfa, "sayfa_sayisi": sayfa_sayisi, "toplam": toplam}


def sayfa_bilgisi(toplam, sayfa, boy):
    sayfa_sayisi = max(1, math.ceil(toplam / boy))
    return {"sayfa": min(max(1, sayfa), sayfa_sayisi), "sayfa_sayisi": sayfa_sayisi, "toplam": toplam}
