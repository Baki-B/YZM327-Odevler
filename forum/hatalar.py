class KuralHatasi(Exception):
    """Forum kurallarına aykırı bir istek. Mesajı doğrudan kullanıcıya gösterilir."""


def tamsayi(deger, mesaj="Sayı bekleniyordu."):
    """Formdan ya da JSON'dan gelen değeri tam sayıya çevirir. Boşsa None; çevrilemiyorsa KuralHatasi.

    Kullanıcı girdisi hiçbir yerde doğrudan int() ile çevrilmez: "abc", "1.5" ya da "²" gibi değerler
    500 hatası yerine kullanıcıya anlaşılır bir uyarı olarak döner."""
    if deger is None or (isinstance(deger, str) and not deger.strip()):
        return None
    try:
        return int(str(deger).strip())
    except ValueError:
        raise KuralHatasi(mesaj) from None
