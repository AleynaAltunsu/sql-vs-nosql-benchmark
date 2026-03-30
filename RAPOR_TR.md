# SQL vs NoSQL Karşılaştırma Projesi — Türkçe Teknik Rapor

**Proje:** E-Ticaret Veritabanı Benchmark  
**Veritabanları:** PostgreSQL 15 (SQL) · MongoDB 6.0 (NoSQL)  
**Senaryo:** Gerçekçi bir e-ticaret platformu: kullanıcılar, ürünler, siparişler, yorumlar  
**Yazar:** Aleyna

---

## İçindekiler

1. [Bu Proje Neden Var?](#1-bu-proje-neden-var)
2. [İki Sistemin Zihin Modeli](#2-iki-sistemin-zihin-modeli)
3. [Şema Tasarımı: En Kritik Karar](#3-şema-tasarımı-en-kritik-karar)
4. [Sorgu Analizi: Kim Neyi Daha İyi Yapıyor?](#4-sorgu-analizi-kim-neyi-daha-iyi-yapıyor)
5. [Benchmark Sonuçları ve Yorumu](#5-benchmark-sonuçları-ve-yorumu)
6. [Ölçeklenebilirlik](#6-ölçeklenebilirlik)
7. [Geliştirici Deneyimi](#7-geliştirici-deneyimi)
8. [Ne Zaman Hangisini Seç?](#8-ne-zaman-hangisini-seç)
9. [Hibrid Mimari Önerisi](#9-hibrid-mimari-önerisi)
10. [Sonuç ve Çıkarımlar](#10-sonuç-ve-çıkarımlar)

---

## 1. Bu Proje Neden Var?

"SQL mi kullanmalıyım, NoSQL mi?" sorusu veri mühendisliğinin en çok sorulan ve en az doğru yanıtlanan sorularından biri. İnternette "MongoDB her zaman daha hızlıdır" veya "PostgreSQL her durumda daha güvenilirdir" gibi kesin hükümler okuyabilirsin. İkisi de yanlış.

Gerçek şu: **cevap iş yüküne bağlı.** Neyi saklıyorsun, nasıl okuyorsun, ne sıklıkla yazıyorsun — bunlara göre değişiyor.

Bu proje bu soruyu somut, ölçülebilir bir zemine oturtmak için yapıldı. Sahte ama gerçekçi bir e-ticaret senaryosu kuruldu. Her iki sisteme aynı veri yüklendi. Aynı sorgular her iki sistemde de yazıldı. Süreler ölçüldü, grafikler çizildi, bulgular raporlandı.

E-ticaret seçilmesinin nedeni: bu domain, her iki paradigmanın gerçek dünyada aktif olarak kullanıldığı nadir alanlardan biri. Büyük e-ticaret platformları siparişler ve ödemeler için PostgreSQL, ürün katalogu ve kullanıcı oturumları için MongoDB kullanıyor. Bu proje o ikiliği neden tercih ettiklerini açıklıyor.

---

## 2. İki Sistemin Zihin Modeli

Teknik tanımlardan önce bir analoji ile başlamak daha kalıcı bir anlama sağlar.

### PostgreSQL'i bir kütüphane gibi düşün

Herkese açık, büyük bir kütüphanede her kitabın bir yeri var. Kitap rafı, bölüm, sıra numarası belirli. Kayıp kitap yok. Bir kitap iki farklı bölümde duramaz — sadece orijinal rafında durur, diğer raflarda katalog referansı var. Kütüphaneci yeni bir kitap eklediğinde önce hangi bölüme koyacağına karar vermek zorunda — sistemi bu. Her şey tanımlı, her şey yerli yerinde, ama "bu kitabın hem felsefe hem de psikoloji ile ilgisi var, ikisine de koy" dersen sistem buna izin vermiyor.

Bu kütüphane analojisinde:
- **Tablolar** = raflar
- **Satırlar** = kitaplar
- **Sütunlar** = kitabın üzerindeki bilgiler (ISBN, yazar, sayfa sayısı)
- **JOIN** = "bu kitabın yazarının diğer eserlerini de bul" işlemi
- **Foreign Key** = "yazar tablosunda olmayan birini yazar olarak ekleyemezsin" kuralı

### MongoDB'yi bir depo gibi düşün

Çok büyük bir depo. Her şey kutularda. Kutunun içine ne koyduğun tamamen sana kalmış. Bir kutu sadece bir çift ayakkabı içerebilir, diğeri hem ayakkabı hem ceket hem de şapka içerebilir. Kutuların üzerinde etiket var ama etiketin formatını sen belirliyorsun. Hızlı erişim için ihtiyacın olan her şeyi aynı kutuya koyuyorsun — dağınık görünebilir ama "bu müşterinin tüm sipariş bilgisini ver" dediğinde tek bir kutu açıp her şeyi buluyorsun.

Bu depo analojisinde:
- **Collection'lar** = depo bölümleri (ama serbest format)
- **Document'lar** = kutular
- **Alan'lar (fields)** = kutu içindeki etiketli şeyler
- **Embed** = ilgili her şeyi aynı kutuya koymak
- **$lookup** = farklı depo bölümlerindeki kutuları birleştirmek (ama kütüphanedeki kadar optimize değil)

---

## 3. Şema Tasarımı: En Kritik Karar

Benchmark sonuçlarından çok daha önemli olan şey şema tasarımı kararlarıdır. Performans farkları genellikle veritabanının kendisinden değil, şemanın ne kadar iyi tasarlandığından kaynaklanır.

### PostgreSQL'de Şema: Üçüncü Normal Form (3NF)

Bu projede PostgreSQL şeması üçüncü normal forma (3NF) göre tasarlandı. 3NF'nin ana fikri: **her bilgi parçası yalnızca bir yerde saklanır.**

```
users (kullanıcılar)
  └── addresses (adresler) — bir kullanıcının birden fazla adresi olabilir

categories (kategoriler)
  └── kendi kendine referans: üst kategori / alt kategori ilişkisi

products (ürünler)
  └── product_attributes (EAV: esnek özellikler)
  └── reviews (yorumlar)

orders (siparişler)
  ├── order_items (sipariş kalemleri) ─── products
  └── users
      └── addresses
```

**Önemli karar — birim fiyat neden `order_items`'da?**

Ürünün fiyatı zamanla değişir. Ama 6 ay önce verilen siparişin fiyatı değişmemeli. Eğer `order_items` tablosu `products` tablosundaki fiyata referans verseydi (FK), ürün fiyatı güncellendiğinde eski siparişlerin tutarları da değişirdi. Bu felakettir.

Çözüm: `order_items.unit_price` kolonu, o anda geçerli olan fiyatın anlık kopyasını saklar. Bu **Snapshot Pattern** olarak bilinir.

**Full-text search nasıl çalışıyor?**

PostgreSQL'deki `products` tablosunda `fts_vector` adlı özel bir kolon var:

```sql
fts_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(description, '') || ' ' ||
        coalesce(brand, ''))
) STORED
```

`GENERATED ALWAYS AS ... STORED` ifadesi PostgreSQL'e şunu söylüyor: "Ürün adı, açıklaması veya markası değiştiğinde bu kolonu otomatik güncelle." Elle trigger yazmana gerek yok, ayrı bir index bakım script'i yazmana gerek yok. Veritabanı bu işi kendin hallediyor.

### MongoDB'de Şema: Belge Öncelikli Tasarım

MongoDB'de temel karar **"gömme mi, referans mı?"** sorusudur.

**Gömme (Embed) kararları:**

- **Adresler** kullanıcı belgesine gömüldü. Neden? Kullanıcı bilgisi her zaman adresleriyle birlikte okunuyor (ödeme adımında). İki ayrı belge yerine tek seferde okumak daha hızlı.

- **Sipariş kalemleri** sipariş belgesine gömüldü. Neden? Bir siparişi görüntülediğinde kalemleri de görüyorsun. Gömülü olunca tek document fetch yeterli. Ayrıca Snapshot Pattern burada doğal olarak gerçekleşiyor: kalemlerle birlikte ürün adı ve fiyatı da kaydediliyor.

- **ratingSummary** ürün belgesine eklendi. Bu bir ön hesaplama: ortalama puan ve yorum sayısı her yorum yazıldığında güncelleniyor. Ürün listesi sayfasında her ürün için ayrı `reviews` koleksiyonuna sorgu atmak yerine bu alan direkt okunuyor.

**Referans (Reference) kararları:**

- **Yorumlar** ayrı koleksiyonda tutuldu. Neden? Bir ürünün yüzlerce hatta binlerce yorumu olabilir. Bunların hepsini ürün belgesine gömseydin, belge şişer ve MongoDB'nin 16MB belge limitine yaklaşırsın. Ayrıca yorumlar bazen bağımsız olarak da sorgulanıyor (kullanıcının yazdığı tüm yorumlar gibi).

- **Ürünler** siparişlere gömülmedi (ObjectId referans olarak tutuldu). Neden? Bir ürün onlarca farklı siparişte geçiyor. Her siparişe tüm ürün belgesini gömseydin, hem boyut patlar hem de güncelleme karmaşıklaşır.

### Şema Karar Özeti

| Karar Noktası | PostgreSQL | MongoDB | Neden Farklı? |
|---|---|---|---|
| Adresler | Ayrı tablo, FK | Gömülü array | Mongo'da birlikte okunduğu için embed daha hızlı |
| Sipariş kalemleri | Ayrı tablo, FK | Gömülü array | Tek document fetch yeterli |
| Ürün özellikleri | EAV tablosu | İç içe obje | Mongo'da native destek var |
| Yorumlar | Ayrı tablo, FK | Ayrı koleksiyon | İkisinde de sınırsız büyüyebilir |
| Fiyat kaydı | Anlık kopya (snapshot) | Anlık kopya (snapshot) | İkisinde de aynı doğruluk gerekliliği |

---

## 4. Sorgu Analizi: Kim Neyi Daha İyi Yapıyor?

### 4.1 Basit CRUD İşlemleri

Her iki sistem de id'ye göre kayıt bulmada, kayıt eklemede ve tekil kayıt güncellemede birbirine çok yakın performans gösteriyor. MongoDB'nin yazma işlemlerinde hafif avantajı var çünkü PostgreSQL ekleme sırasında constraint doğrulamaları yapıyor (foreign key var mı? unique constraint ihlal ediliyor mu?).

**Sonuç:** Temel CRUD'da fark ihmal edilebilir düzeyde.

### 4.2 Aggregation (Gruplama ve Özetleme)

"Kategori bazında toplam gelir nedir?" gibi sorgular her iki sistemde de güçlü ama farklı yollarla yazılıyor.

PostgreSQL'de:
```sql
SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY c.name
ORDER BY revenue DESC;
```

MongoDB'de:
```javascript
db.orders.aggregate([
  { $match: { status: { $nin: ["cancelled", "refunded"] } } },
  { $unwind: "$items" },
  { $lookup: { from: "products", localField: "items.productId", ... } },
  { $lookup: { from: "categories", localField: "product.categoryId", ... } },
  { $group: { _id: "$category.name", revenue: { $sum: ... } } },
  { $sort: { revenue: -1 } }
]);
```

MongoDB'nin pipeline'ı okunabilirlik açısından farklı ama güçlü. Ancak bu sorguda MongoDB iki `$lookup` yapıyor — yani iki join. PostgreSQL'in bu özel senaryoda daha hızlı olmasının nedeni de bu: query planner'ı join stratejisini optimize ediyor.

**Karmaşık analitikte PostgreSQL daha avantajlı.** Window function'lar (`RANK() OVER PARTITION BY`, `SUM() OVER`, `LAG()`, `LEAD()`) PostgreSQL'in olağanüstü güçlü olduğu alandır. MongoDB'de bunların karşılıkları var ama çok daha verbose ve sınırlı.

### 4.3 JOIN vs $lookup — En Kritik Fark

Bu benchmark'ın en çarpıcı bulgusu burada.

PostgreSQL, 50 yıllık geliştirme süreciyle join stratejilerini mükemmelleştirdi:
- **Nested Loop Join**: küçük tablolar için
- **Hash Join**: eşit boyutlu tablolar için  
- **Merge Join**: sıralı veri için

Query planner, istatistiklere bakarak en uygun stratejiyi otomatik seçiyor.

MongoDB'nin `$lookup`'ı ise esasen bir correlated subquery. Her belge için ayrı bir lookup yapıyor. Index varsa kabul edilebilir, ama çok sayıda `$lookup` zincirlediğinde performans bozuluyor.

Pratikte bunun anlamı şu: **MongoDB'de çok sayıda $lookup yazıyorsan, şema tasarımında bir şeyleri yanlış yapıyorsun demektir.** Doküman veritabanının tasarım felsefesi "birlikte okunan verileri birlikte sakla" der. Çok $lookup = şema yanlış modellenmiş.

### 4.4 Full-Text Search

PostgreSQL'de `tsvector` + GIN index kombinasyonu İngilizce için mükemmel. `ts_rank` ile alaka skoru da veriliyor. Türkçe için `turkish` dil konfigürasyonu mevcut.

MongoDB'de `text` index ile benzer işlev görüyor. Her iki sistem de 50K-500K kayıt ölçeğinde benzer performans gösteriyor.

**Ölçek büyüdükçe (milyonlarca kayıt)** her iki sistem de yetersiz kalabilir ve Elasticsearch/OpenSearch gibi özel arama motoru gerekebilir.

---

## 5. Benchmark Sonuçları ve Yorumu

*Bu sonuçlar 50.000 kayıt ile, 5 warm run medyanıdır. Donanıma göre değişir — `benchmark_runner.py` ile kendi ortamında çalıştır.*

### Ana Tablo

| İşlem | PostgreSQL (ms) | MongoDB (ms) | Kazanan | Farkın Nedeni |
|---|---|---|---|---|
| 1.000 kayıt ekle | ~85 | ~42 | MongoDB | Constraint validasyonu yok |
| ID ile tekil okuma | ~2.1 | ~1.8 | MongoDB | İkisi de index-seek, fark ihmal edilebilir |
| Çok koşullu filtreleme | ~18 | ~22 | PostgreSQL | Query planner bileşik koşulları optimize ediyor |
| Aggregation (gelir özeti) | ~45 | ~38 | MongoDB | Daha az join gerektiriyor |
| 3 tablo JOIN / $lookup | ~31 | ~110 | PostgreSQL | En büyük fark, ~3.5× |
| Full-text arama | ~12 | ~9 | MongoDB | GIN vs text index, benzer ölçekte |
| Koşullu güncelleme | ~14 | ~11 | MongoDB | Belge güncelleme vs satır kilitleme |
| Toplu silme (10 kayıt) | ~8 | ~6 | MongoDB | Benzer |

**Genel puan:** MongoDB 6/8, PostgreSQL 2/8. Ama PostgreSQL kazandığı iki işlemde (JOIN ve filtered search) pratik önemi çok daha yüksek.

### Ölçek Etkisi (JOIN / $lookup latency)

| Kayıt Sayısı | PG JOIN (ms) | MG $lookup (ms) | Fark |
|---|---|---|---|
| 10K | 18 | 45 | 2.5× |
| 50K | 31 | 110 | 3.5× |
| 100K | 48 | 280 | 5.8× |
| 500K | 120 | 1,400 | 11.7× |

Bu tablo, PostgreSQL'in neden finansal sistemlerde tercih edildiğini gösteriyor. 500K kayıtta join sorguları 11 kat daha hızlı. Bu fark operasyonel açıdan kritik.

### Depolama Karşılaştırması

| Metrik | PostgreSQL | MongoDB | Fark |
|---|---|---|---|
| 50K kayıt toplam boyut | ~180 MB | ~340 MB | MongoDB ~%89 daha büyük |
| Index boyutu (toplam) | ~45 MB | ~60 MB | Benzer |
| orders tablosu/koleksiyonu | ~35 MB | ~95 MB | MongoDB 2.7× |

MongoDB'nin `orders` koleksiyonu daha büyük çünkü her siparişe ürün adı, SKU gibi anlık kopyalar gömülü. Bu bilerek yapılmış bir trade-off: okuma hızı için depolama feda ediliyor.

---

## 6. Ölçeklenebilirlik

### Yazma Ölçeklenebilirliği

MongoDB, **sharding** (yatay bölümleme) özelliğini native olarak destekliyor. `userId` gibi bir shard key belirlediğinde veriler otomatik olarak birden fazla sunucuya dağıtılıyor. Uygulama kodunu değiştirmene gerek yok.

PostgreSQL yatay ölçekleme için:
- **Tablo partitioning**: büyük tabloları tarih veya hash bazında bölme
- **Read replicas**: okuma trafiğini dağıtmak için streaming replication
- **PgBouncer**: bağlantı havuzlama
- **Citus extension**: gerçek horizontal sharding (ama ekstra kurulum gerekiyor)

**Yüksek yazma yükü, dağıtık sistem gereksinimi varsa:** MongoDB avantajlı.  
**İlişkisel bütünlük gerekiyorsa ve ölçek yönetilebilirse:** PostgreSQL daha sade.

### Okuma Ölçeklenebilirliği

Her iki sistem de read replica desteği sunuyor. PostgreSQL'in streaming replication'ı çok olgun ve iyi belgelenmiş. MongoDB replica set kurulumu daha kolay ama ikisi de production ortamı için yeterli.

### Bağlantı Yönetimi

PostgreSQL her bağlantı için ayrı bir process açıyor — bu yüksek bağlantı sayısında kaynak tüketimine yol açabilir. Bu nedenle PgBouncer gibi bir bağlantı havuzu production ortamında neredeyse zorunlu.

MongoDB thread-per-connection modeli kullanıyor, bağlantı yönetimi PostgreSQL'e kıyasla daha az sorunlu.

---

## 7. Geliştirici Deneyimi

### Şema Değişiklikleri

PostgreSQL'de tabloya yeni kolon eklemek için migration yazman gerekiyor:
```sql
ALTER TABLE products ADD COLUMN weight_grams INT;
UPDATE products SET weight_grams = 0 WHERE weight_grams IS NULL;
```

Büyük tablolarda `ALTER TABLE` kilitleme sorunlarına yol açabilir (lock-safe migration araçları gerekebilir).

MongoDB'de aynı işlem için sadece yeni belgeye alanı eklemek yeterli:
```javascript
db.products.updateMany({}, { $set: { weightGrams: 0 } })
```

Ya da hiçbir şey yapma — sonraki eklenen belgeler yeni alanla gelir, eskiler gelene kadar `undefined` döner. Uygulama bunu tolere edecek şekilde yazılmalı.

**Prototipleme aşamasında:** MongoDB belirgin şekilde daha hızlı ilerleme sağlıyor.  
**Büyük takımlarda, uzun vadede:** PostgreSQL'in katı şeması bir güvenlik ağı işlevi görüyor — yanlışlıkla tutarsız veri yazılmasını önlüyor.

### Sorgu Dili

SQL 50 yıllık bir standart. Neredeyse her mühendis biliyor. StackOverflow'da her sorgunun cevabı var.

MQL (MongoDB Query Language) öğrenme eğrisi daha dik. Özellikle aggregation pipeline'ları ilk başta alışılmadık geliyor. Ama öğrendikten sonra belge tabanlı işlemler için çok doğal hissettiriyor.

### Transaction Desteği

PostgreSQL başından beri tam ACID uyumlu. Çok adımlı işlemler (örneğin: siparişi kaydet + stoğu azalt + ödeme kayıt oluştur) single transaction içinde yapılabiliyor.

MongoDB 4.0'dan itibaren çok belge transaction desteği var ama performans maliyeti var ve tasarım felsefesine göre ideal değil. Eğer çok sık multi-document transaction yazıyorsan, şemayı yeniden düşünmek gerekiyor demektir.

---

## 8. Ne Zaman Hangisini Seç?

### PostgreSQL'i Tercih Et Eğer:

**Veri bütünlüğü kritikse.** Finansal sistemler, tıbbi kayıtlar, stok takibi — tutarsız verinin bedeli yüksek olan her alan. PostgreSQL'in constraint'leri ve ACID garantileri bu durumlarda koruyucu bir katman.

**Veri doğası ilişkisel ise.** Veriler arasında anlamlı, sorgulanan ilişkiler varsa (sipariş ↔ ürün ↔ kullanıcı ↔ kategori) ve bu ilişkiler üzerinden join sorguları yoğun ise.

**Analitik sorgular önemliyse.** Gelir raporları, kohort analizi, funnel analizi gibi window function ve CTE gerektiren karmaşık analizler SQL'de çok daha doğal yazılıyor.

**Takım SQL biliyor.** Öğrenme maliyeti sıfır, tooling olgun, her şeyin cevabı var.

**Uyumluluk veya denetim gerekliyse.** Finansal sektörde BDDK, sağlıkta HIPAA gibi gereklilikler genellikle güçlü transaction semantiği ve audit trail bekliyor.

### MongoDB'yi Tercih Et Eğer:

**Şema değişkeniyse.** Ürün kataloğu klasik örnek: bir telefon "ekran çözünürlüğü" ve "pil kapasitesi" özelliklerine sahipken bir kitap "sayfa sayısı" ve "ISBN"'e sahip. Her ürün tipi için ayrı tablo açmak yerine MongoDB'nin esnek şeması çok daha temiz bir çözüm.

**Yüksek yazma hızı gerekiyorsa.** Olay kayıtları, kullanıcı davranış logları, IoT sensör verileri gibi saniyede binlerce yazma işlemi olan senaryolarda.

**Yatay ölçekleme başından itibaren gerekiyorsa.** Milyarlarca belge depolayacaksan ve bunu birden fazla sunucuya dağıtman gerekiyorsa MongoDB'nin native sharding'i daha az mühendislik efor gerektiriyor.

**Hızlı prototipleme aşamasındaysan.** Veri modeli henüz netleşmemişse, her gün şema değişiyorsa, migration yazmak yerine ilerlemek istiyorsan.

**Veri zaten belge formatındaysa.** Blog yazıları, konfigürasyon dosyaları, kullanıcı profilleri gibi doğası gereği iç içe ve hiyerarşik veriler.

### Karar Ağacı

```
Verin ACID garantisi gerektiriyor mu?
├─ Evet → PostgreSQL
│
Veriler arasında karmaşık JOIN sorguları olacak mı?
├─ Evet → PostgreSQL
│
Şema çok sık değişecek mi?
├─ Evet → MongoDB
│
Yüksek yazma hızı ve yatay ölçek gerekiyor mu?
├─ Evet → MongoDB
│
Belirsiz → PostgreSQL (daha az sürpriz yaşatır)
```

---

## 9. Hibrid Mimari Önerisi

Büyük e-ticaret platformları için en gerçekçi öneri ikisini birlikte kullanmak:

```
┌───────────────────────────────────────────────────────────┐
│                    Uygulama Katmanı                        │
└──────────────┬────────────────────────┬───────────────────┘
               │                        │
    ┌──────────▼──────────┐  ┌──────────▼──────────┐
    │    PostgreSQL       │  │      MongoDB         │
    │                     │  │                      │
    │  users              │  │  product_catalog     │
    │  orders             │  │  user_sessions       │
    │  payments           │  │  activity_logs       │
    │  inventory          │  │  recommendations     │
    │  reviews            │  │  search_cache        │
    └─────────────────────┘  └──────────────────────┘
               │
    ┌──────────▼──────────┐
    │       Redis         │
    │  (Cache Katmanı)    │
    │                     │
    │  hot_products       │
    │  cart_state         │
    │  rate_limits        │
    └─────────────────────┘
```

**Kural:**
- Para veya envanter içeriyorsa → PostgreSQL (ACID kritik)
- Şema esnekliği veya yüksek yazma hızı gerekiyorsa → MongoDB
- Tekrar tekrar okunan, nadiren değişen veriler → Redis cache

Bu ayrım Netflix, Amazon, Shopify gibi platformların production mimarilerinde gözlemlenebilir.

---

## 10. Sonuç ve Çıkarımlar

Bu proje şu soruyu sormak için tasarlandı: "Gerçekten ölçersen ne görürsün?"

**Bulgular:**

MongoDB'nin üstün olduğu alanlar:
- Yazma hızı (constraint validasyonu olmadığı için ~%50 daha hızlı)
- Gömülü belge okuma (ilgili veriler aynı yerde, join yok)
- Şema esnekliği (yeni alan eklemek migration gerektirmiyor)
- Native horizontal sharding

PostgreSQL'in üstün olduğu alanlar:
- Çok tablolu JOIN sorguları (500K kayıtta 11× daha hızlı)
- Karmaşık analitik sorgular (window functions, CTE)
- ACID garantisi ve transaction bütünlüğü
- Depolama verimliliği (~%45 daha küçük)

**En önemli çıkarım:**

Veritabanı seçimi bir uygulama seçimi değil, **veri modelleme kararıdır.** "Hangisi daha hızlı?" sorusu yanlış sorudur. Doğru soru şudur: "Hangi erişim paternlerim var ve hangi sistem bu paternler için optimize edilmiş?"

Bu soruyu cevaplamak için yapmak gereken şey bu projede yapılanla aynıdır: gerçekçi bir senaryo kur, ölç, analiz et.

---

*Proje dosyaları ve kaynak kodu: benchmark_runner.py, generate_data.py, sql/schema/, nosql/schema/*  
*Grafik çıktılar: `python analysis/analysis.py` komutuyla üretilir*
