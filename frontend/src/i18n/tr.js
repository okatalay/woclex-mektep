export const tr = {
  brand: 'Mektep',
  errors: {
    network: 'Sunucuya ulaşılamıyor. Bağlantını kontrol edip tekrar dene.',
    error: 'İşlem tamamlanamadı. Biraz sonra tekrar dene.',
    not_authenticated: 'Oturumun sona erdi. Tekrar giriş yap.',
    invalid_credentials: 'Kullanıcı adı veya şifre hatalı.',
    too_many_attempts: 'Çok fazla hatalı deneme. Birkaç dakika sonra tekrar dene.',
    forbidden: 'Bu işlem için yetkin yok.',
    not_found: 'Kayıt bulunamadı veya erişimin yok.',
    username_taken: 'Bu kullanıcı adı alınmış.',
    invalid_username: 'Kullanıcı adı 3–32 karakter olmalı: küçük harf, rakam, nokta, tire veya alt çizgi.',
    join_code_not_found: 'Bu katılım kodu geçerli değil. Eğitmeninden yeni bir kod veya link iste.',
    invite_not_found: 'Bu davet linki geçersiz veya süresi dolmuş. Eğitmenden yeni bir link iste.',
    required: 'Bu alan zorunlu.',
    invalid: 'Geçersiz değer.',
    string_too_short: 'Çok kısa.',
    string_too_long: 'Çok uzun.',
    string_pattern_mismatch: 'Biçim geçersiz.',
    student_not_found: 'Öğrenci bulunamadı veya erişimin yok.',
    classroom_not_found: 'Sınıf bulunamadı veya erişimin yok.',
    no_valid_students: 'En az bir öğrenci seç.',
    file_too_large: 'Dosya çok büyük (en fazla 20 MB).',
    already_reviewed: 'Bu teslim incelendi, artık değiştirilemez.',
    template_has_no_stops: 'Önce şablona durak ekle.',
    invalid_submission_types: 'En az bir teslim türü seç.',
    invalid_kind: 'Geçersiz çizelge türü.',
    invalid_status: 'Geçersiz durum.',
    invalid_page_range: 'Bitiş sayfası başlangıçtan küçük olamaz.',
    category_not_found: 'Başlık bulunamadı.',
    item_not_found: 'Konu bulunamadı.',
    log_not_found: 'Kayıt bulunamadı.',
  },
  role: { owner: 'Kurum Sahibi', admin: 'Yönetici', teacher: 'Eğitmen', student: 'Öğrenci', guardian: 'Veli' },
}

export function errText(err, field) {
  if (!err) return ''
  const code = field ? err.fields?.[field] : err.code || Object.values(err.fields || {})[0]
  return tr.errors[code] || tr.errors[err.code] || tr.errors.error
}
