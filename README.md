# Football Quant Engine — Q200

Temizden oluşturulmuş, test odaklı futbol olasılık analiz çekirdeği.

## Tasarım

Q200 iki aşamalı çalışır:

1. **MODEL AŞAMASI**
   - İstatistik verileri
   - λ Home / λ Away
   - Poisson
   - Model olasılıkları
   - 100.000+ Monte Carlo
   - Model LOCK

2. **ORAN AŞAMASI**
   - Oran doğrulama
   - Vig / No-Vig
   - Fair Odds
   - EV
   - Value
   - Belirsizlik eşiği
   - Quarter Kelly
   - Maksimum %2 bankroll riski

Oranlar model oluşturulurken kullanılmaz.

## Q200 λ formülü

HOME:
`0.35 × Home Home GF + 0.35 × Away Away GA + 0.15 × Home Home xG + 0.15 × Away Away xGA`

AWAY:
`0.35 × Away Away GF + 0.35 × Home Home GA + 0.15 × Away Away xG + 0.15 × Home Home xGA`

xG/xGA eksikse ağırlıklar mevcut bileşenler arasında normalize edilir.

## EV eşikleri

- LOW: +5%
- MEDIUM: +8%
- HIGH: +12%
- VERY_HIGH: seçim yok

Minimum oran: **1.50**

Bu yazılım herhangi bir bahis sonucunu garanti etmez; yalnızca verilen veriler üzerinden matematiksel analiz üretir.

## Yerelde çalıştırma

```bash
pip install -r requirements.txt
pytest -q
```

Beklenen sonuç: tüm testlerin geçmesi.
