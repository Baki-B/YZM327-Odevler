"""S01-49 uygulamalı soru 6: bir YZ kodlama aracının yazdığı fonksiyon (ilk öneri, değiştirilmeden kaydedildi)."""


def tc_kimlik_gecerli(no) -> bool:
    """Verilen değerin geçerli bir T.C. kimlik numarası olup olmadığını döndürür.

    Kurallar:
      - 11 haneli olmalı ve yalnızca ASCII rakamlardan oluşmalı,
      - ilk hane 0 olamaz,
      - 10. hane = ((1,3,5,7,9. hanelerin toplamı * 7) - (2,4,6,8. hanelerin toplamı)) mod 10,
      - 11. hane = ilk 10 hanenin toplamının mod 10 değeri.

    Baştaki ve sondaki boşluklar kırpılır; başka her şey geçersizdir.
    """
    if not isinstance(no, str):
        return False

    no = no.strip()

    if len(no) != 11:
        return False
    if not all(c in "0123456789" for c in no):
        return False
    if no[0] == "0":
        return False

    d = [int(c) for c in no]

    tek = d[0] + d[2] + d[4] + d[6] + d[8]
    cift = d[1] + d[3] + d[5] + d[7]

    if (tek * 7 - cift) % 10 != d[9]:
        return False
    if sum(d[:10]) % 10 != d[10]:
        return False

    return True
