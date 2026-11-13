# SAHTE ÖRNEK DOSYA — Kod Bilimi Atölyesi'nin "Gizli bilgi sızıntısı" paketi için.
# Buradaki bütün "gizli" değerler uydurmadır; hiçbir hizmette geçerli değildir.
# AKIA ile başlayan anahtar, AWS belgelerinde yayımlanan resmî örnek anahtardır.

VERITABANI = "sqlite:///ornek.db"
password="ORNEK-SAHTE-PAROLA-123"
API_KEY = "ornek-sahte-anahtar-0000"
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"


def baglan():
    # Doğrusu: değerleri ortam değişkeninden okumak (os.environ) ve depoya koymamak.
    return VERITABANI
