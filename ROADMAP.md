# Neon Racer Yol Haritası

Kurallar:

- Her adımın sonunda oyun oynanabilir kalmalı.
- Oyun her adımda tarayıcıda (pygbag) ve telefonda çalışmalı.
- İleride oyunu Unity'ye taşımak mümkün olabilir. Kod buna engel olmayacak şekilde düzenli tutulmalı.

## 1. Hızlı kazanımlar

- [x] Synthwave arka plan müziği ve ses efektleri: şerit değiştirme, boost, çarpışma ve başlangıç sesleri. Sesler kodla üretilsin (`tools/make_sounds.py`, numpy) ve `assets/` içine `.ogg` olarak kaydedilsin.
- [x] Ses aç/kapat: M tuşu ve menüde hoparlör simgesi.
- [x] Kalıcı en iyi skor: tarayıcıda localStorage, bilgisayarda `save.json`. Rekor kırılınca "YENİ REKOR!" yazısı çıksın.
- [x] Telefonda sola/sağa kaydırarak şerit değiştirme. Dokunarak değiştirme de çalışmaya devam etsin.

## 2. Altın ve kalkan

- [ ] Yolda toplanabilir altın paralar. Toplam altın kaydedilsin ve ekranda görünsün.
- [ ] Kalkan güçlendirmesi: bir çarpışmayı affeder.

## 3. Mağaza

- [ ] Altınla açılan, farklı renk ve şekillerde arabalar. Seçilen araba kaydedilsin.

## 4. Çeşitli trafik ve görevler

- [ ] Şerit değiştiren arabalar, yavaş kamyonlar, polis.
- [ ] Küçük görevler (ör. "tek oyunda 3 boost topla") ve ödülleri.

## 5. Grafik güçlendirme

- [ ] Daha detaylı araba modelleri: farlar, yansımalar, tekerlek dönme animasyonu, fren lambası parlaması.
- [ ] Gelişmiş ışık: yola vuran far ışığı, lambaların yolda yansıması, ıslak asfalt efekti.
- [ ] Daha zengin arka plan: hareket eden bulutlar, kayan yıldızlar, uzakta yanıp sönen şehir ışıkları.
- [ ] Ekran efektleri: hıza göre bulanıklık, boost'ta kromatik sapma (renk kayması), CRT/scanline seçeneği.
- [ ] Daha güçlü parçacıklar: çarpışmada metal kıvılcımları ve duman, altın toplarken parıltı.
- [ ] Arayüz: neon çerçeveli menüler, animasyonlu geçişler, daha iyi yazı tipi.

## 6. Temalar ve performans

- [ ] Mesafeye göre değişen bölgeler/temalar: şehir, çöl, tünel, gece/gündüz.
- [ ] Mobilde akıcı çalışması için grafik kalite ayarı (Düşük/Orta/Yüksek). Telefonda varsayılan Orta olsun.
