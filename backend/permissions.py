"""İzin kodları ve sistem rolleri. Tek doğruluk kaynağı; frontend gerekirse /api/auth/me'den okur."""

# (kod, grup, Türkçe etiket)
PERMISSIONS = [
    ("org.manage", "Kurum", "Kurum bilgilerini yönet"),
    ("members.manage", "Kurum", "Eğitmenleri yönet"),
    ("classroom.manage_all", "Sınıf", "Kurumun tüm sınıflarını yönet"),
    ("classroom.create", "Sınıf", "Sınıf oluştur"),
    ("classroom.manage_own", "Sınıf", "Kendi sınıflarını yönet"),
    ("student.manage", "Öğrenci", "Öğrenci ekle/çıkar, veli davet et"),
    ("assignment.manage", "Ödev", "Ödev oluştur ve ata"),
    ("submission.review", "Teslim", "Teslimleri incele ve puanla"),
    ("announcement.manage", "Duyuru", "Duyuru yayınla"),
    ("tracking.manage", "Takip", "Yoklama, ezber/tecvid ve sayfa takibi işle"),
]
ALL_CODES = [p[0] for p in PERMISSIONS]

_TEACHER_CODES = [
    "classroom.create", "classroom.manage_own", "student.manage",
    "assignment.manage", "submission.review", "announcement.manage", "tracking.manage",
]

# system_key -> (ad, izinler). Owner her zaman tüm izinler; düzenlenemez.
SYSTEM_ROLES = {
    "owner": ("Kurum Sahibi", ALL_CODES),
    "admin": ("Yönetici", [c for c in ALL_CODES if c != "org.manage"]),
    "teacher": ("Eğitmen", _TEACHER_CODES),
    "student": ("Öğrenci", []),
    "guardian": ("Veli", []),
}
