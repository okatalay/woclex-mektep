# Mektep

Kur'an-Tecvid öğrenci-veli-eğitmen takip platformu: eğitmen sınıf açar, öğrenci sınıf koduyla/linkle katılır, eğitmen ödev atar, öğrenci teslim eder (ses/metin/dosya), veli ve eğitmen gelişimi izler, üç rol arası mesajlaşma. Kurum yapısı (çok eğitmenli) baştan var. Yayın adresi (planlanan): `mektep.woclex.com`.

Kullanıcıyla iletişim Türkçe, kısa. Arayüz metinleri Türkçe (tek yerde: `frontend/src/i18n/tr.js`).

Mimari ve tasarım kararları `woclex-portfoy`'dan uyarlandı (kanıtlanmış desen); farklılıklar için ayrıntılı plan: `.claude/plans/pasted-content-id-755b-merhaba-imdi-memoized-umbrella.md` (workspace kökünde).

## Yapı
- `backend/` FastAPI, düz yerleşim: `routers/`, `services/`, `models/`, `alembic/`, `tests/`. Postgres, SQLAlchemy 2, Alembic (`create_all()` yok).
- `frontend/` Vite + React 18 + react-router 6, düz CSS (`src/styles/`), `lucide-react`, `@fontsource/inter` + `@fontsource/noto-naskh-arabic`.

## Roller ve modeller
- Roller: `owner`, `admin` (kurum), `teacher`, `student`, `guardian`. İzin kodları tek kaynak: `backend/permissions.py`.
- Sınıf: `classrooms` (join_code + join_enabled). Öğrenci `enrollments` ile bağlanır. Veli `guardian_links` ile öğrenciye bağlanır; bağ, eğitmenin öğrenci kartından ürettiği tek kullanımlık `guardian_invites` linkiyle kurulur (7 gün geçerli).
- Nesne erişim kararı yalnız `backend/services/access.py` üzerinden (`can_manage_classroom` vb.). Erişimi olmayan kayıt için 404, yetkisiz eylem için 403.
- V1 sınırı: `memberships.user_id` unique — bir kullanıcı tek kuruma bağlı. Bir velinin farklı kurumlardaki (farklı eğitmenlerin) çocuklarına bağlanması bu sürümde desteklenmiyor.

## Tasarım
- Apple HIG iskeleti (sidebar → mobilde tab bar). Site her zaman açık tema (beyaz/nötr gri); sistem koyu tema tercihi dinlenmiyor (kullanıcı isteği). `data-theme="dark"` tokenları ileride bir tema anahtarı eklenirse hazır duruyor.
- Kimlik: Mushaf yeşili `--accent: #0f5c4a`, Tezhip altını `--gold` (yalnız rozet/başarı için, henüz kullanılmıyor), Arapça içerik için `--font-arabic` (Noto Naskh Arabic).
- Giriş/kayıt/katılım sayfaları iki panelli: sol ince girih desenli yeşil panel + karşılama metni, sağ form (`frontend/src/pages/AuthPages.jsx`, `.auth-*` sınıfları).
- Yeni renk/bileşen önce `frontend/src/styles/tokens.css`.

## Komutlar
- Dev DB: `docker compose up -d` (127.0.0.1:5462). Backend: `cd backend && .venv/bin/uvicorn main:app --port 8065`. Frontend: `cd frontend && npm run dev` (5195, `/api` → 8065).
- Test: `cd backend && .venv/bin/python -m pytest -q tests` (ayrı `mektep_test` veritabanı). Derleme: `cd frontend && npm run build`.
- venv: `python3 -m venv` bu makinede çalışmıyor; `virtualenv .venv` kullan.
- `.env` (gitignore'lu) `.env.example`'dan.

## Durum (Faz 1-3 tamam)
Auth (eğitmen kaydı + kurum, sınıf koduyla öğrenci kaydı, veli davetiyle veli kaydı, giriş/çıkış), sınıf CRUD + kod yenileme, öğrenci listesi/detayı + sınıftan çıkarma, veli daveti üretme, öğrenci detayında veli listesi, velinin "Çocuklarım" sayfası (`/api/guardians/me/children`).

Faz 3: eğitmen sınıfa ödev atar (başlık, açıklama, izin verilen teslim türleri: ses/metin/dosya, opsiyonel son tarih) — ödev oluşturma anında sınıftaki aktif öğrenciler hedeflenir (`assignment_targets`). Öğrenci "Ödevlerim"den teslim eder (metin + ses kaydı MediaRecorder ile tarayıcıda kaydedilir, veya dosya/fotoğraf yüklenir; `services/storage.py`, 20MB limit, `data/uploads/submissions/<id>/`). Eğitmen ödev detayında teslimleri görür, 1-5 puan + yazılı geri bildirim + "tekrar istensin" ile inceler (`reviews`). Veli, bağlı öğrencinin teslimini görebilir (`GET /api/submissions/{id}`, erişim `services/access.py` üzerinden). 25 backend testi geçiyor.

Faz 4: `services/progress.py` ilerlemeyi türetir (atanan/teslim/incelenen/tekrar istenen/ortalama puan/tamamlanma %). `/api/dashboard` role göre eğitmen (sınıf/öğrenci/incelenecek teslim sayısı + son bekleyenler), öğrenci (ilerleme + bekleyen ödevler) veya veli (çocuklar + ilerlemeleri) özetini döner. Öğrenci detayı ve veli "Çocuklarım" sayfaları gerçek ilerleme çubuğu gösterir; veli `/api/guardians/children/{id}/assignments` ile çocuğunun ödev geçmişini, salt-okunur inceleme sheet'iyle teslim içeriğini ve eğitmen geri bildirimini görür (düzenleyemez). 32 backend testi geçiyor.

Faz 5: birebir mesajlaşma (`conversations`/`conversation_members`/`messages`) — eğitmen<->öğrenci ve eğitmen<->veli arası (kişi listesi `services/contacts.py` ile hesaplanır; öğrenci-veli birbirine doğrudan mesaj atamaz). Sidebar/tab bar'da okunmamış sayaç rozeti. Duyurular (`announcements`) tek yönlü: eğitmen sınıf detayından yayınlar, o sınıftaki öğrenci ve bağlı veliler `/panel/duyurular`de görür. Ayrı bir `notifications` tablosu eklenmedi — okunmamış mesaj sayacı ve duyuru akışı V1 için yeterli bildirim mekanizması. 41 backend testi geçiyor.

**Rota (yolculuk) özelliği**: `routes`/`route_stops` — eğitmen sınıf detayından bir rota açar, sırayla durak ekler (her durak arka planda bir `Assignment`, mevcut ödev/teslim/inceleme akışını olduğu gibi kullanır — kod tekrarı yok). Öğrenci "Rotalarım"da yolculuk haritasını görür: tamamlanan durak yeşil onay, sıradaki durak vurgulu "Göreve git" ile mevcut ödev teslim sayfasına gider, sonraki duraklar önceki durak `incelendi` olmadan kilitli kalır (`routers/routes.py` sunucu tarafında hesaplar, öğrenci kilidi açamaz). Durak düzenleme (`PATCH`), silme (`DELETE`, sıralama otomatik yeniden hesaplanır) ve yukarı/aşağı taşıma (`POST .../move`) destekleniyor; sıra alanı `route_stops.order_index` unique olduğu için takas/kaydırma işlemleri geçici sentinel değerle üç adımda yapılır (`routers/routes.py`). V1 kapsamı: veli tarafında ayrı bir rota görünümü henüz eklenmedi (çocuğun durak ödevlerini genel "Ödev geçmişi"nden görebiliyor). 53 backend testi geçiyor.

Faz 6: prod deploy tamam — `mektep.woclex.com` canlıda (`docker-compose.prod.yml`, nginx, Traefik).

Faz 7: mesajlaşmada gönderim sonrası boş ekrana yol açan kritik bir hata düzeltildi (`useLoad`'daki `setData` fonksiyonel güncellemeyi desteklemiyordu; ayrıca `Shell.jsx`'e sayfa çökmelerinde beyaz ekranı önleyen bir `ErrorBoundary` eklendi). Ödev/rota atarken "tüm sınıf" veya seçili öğrenciler hedeflenebiliyor (`StudentPicker.jsx`, `routes.py`'de rota hedef kitlesi `Route.target_student_ids` ile rota genelinde sabitleniyor). Eğitmen ödev oluştururken/detayında materyal (ses/görsel/dosya) ekleyebiliyor (`assignment_attachments`). Geri bildirim geçmişinin tamamı gösteriliyor (`reviews` listesi; eskiden yalnızca son inceleme dönüyordu). Öğrenci, incelenene kadar teslimini (ses dahil) silip yeniden gönderebiliyor (`DELETE /api/me/assignments/{id}/files/{file_id}`). Tilavet arşivi (`library_items`/`library_item_files`, `/panel/tilavet-arsivi`) ve rota arşivi (`route_templates`/`route_template_stops`, `/panel/rota-arsivi`) eklendi: öğretmen içerik/durak şablonlarını bir kere hazırlar, tek tıkla sınıfa veya seçili öğrencilere atar/uygular. Rota yolculuk ekranı (`RouteJourney.jsx`) görsel olarak güçlendirildi (üst özet kart, kesikli bağlantı çizgisi, aktif durak vurgusu). 60 backend testi geçiyor.

Faz 8: Excel referanslı müfredat takip modülü tamam. Yeni izin kodu `tracking.manage` (mevcut owner/admin/teacher rollerine migration'da geriye dönük eklendi). Ezber/tecvid çizelgesi: kurum başına şablon (`curriculum_categories`/`curriculum_items`, `/panel/mufredat`'tan yönetilir — Rota'dan bağımsız, sırasız bir checklist), öğrenci başına durum (`curriculum_status`: -/çalışıyor/tekrar/ezberlendi) öğrenci kartından tek tıkla değiştirilir (`CurriculumChart.jsx`, `editable` prop). Yoklama: sınıf + tarih bazlı toplu kayıt (`attendance_records`, `/panel/siniflar/:id/yoklama`), devam oranı türetilir. Kur'an sayfa takibi: öğrenci başına tarihli sayfa aralığı logu (`page_logs`), öğretmen ekler/siler. Özet: `/api/students/{id}/tracking-summary` (`services/tracking.py`) ezber/tecvid tamamlanma %, devam oranı, güncel sayfa ve toplam okunan sayfayı birleştirip basit bir rozet türetir (Başlangıç/Gümüş/Altın). Öğrenci "Gelişimim" (`/panel/gelisimim`), veli çocuk detayında salt-okunur aynı özeti görür; öğretmen taraflı düzenleme öğrenci kartında (`StudentDetail.jsx`). 67 backend testi geçiyor.

Geçici önizleme: `http://187.124.27.129:5195` (dev sunucu, Traefik/domain yok — yalnızca bakmak için).
