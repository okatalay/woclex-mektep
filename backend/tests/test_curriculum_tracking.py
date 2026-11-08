from tests.helpers import create_classroom, join_as_guardian, join_as_student, solo_teacher


def _class_with_student():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"], full_name="Test Öğrenci")
    sid = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    return teacher, classroom, student, sid


def _guardian_for(teacher, classroom_id, student_id):
    invite = teacher.post(f"/api/classes/{classroom_id}/students/{student_id}/guardian-invite", json={})
    assert invite.status_code == 201, invite.text
    guardian, _ = join_as_guardian(invite.json()["token"])
    return guardian


def test_teacher_builds_ezber_chart_and_sets_status():
    teacher, classroom, student, sid = _class_with_student()

    r = teacher.post("/api/curriculum/categories", json={"kind": "ezber", "title": "SEVİYE 1"})
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]
    r = teacher.post(f"/api/curriculum/categories/{cat_id}/items", json={"title": "Kelime-i Şehadet"})
    assert r.status_code == 201, r.text
    item_id = r.json()["id"]

    r = teacher.get(f"/api/curriculum?kind=ezber&student_id={sid}")
    assert r.status_code == 200, r.text
    assert r.json()["categories"][0]["items"][0]["status"] == "-"

    r = teacher.post(f"/api/curriculum/items/{item_id}/status", json={"student_id": sid, "status": "ezberlendi"})
    assert r.status_code == 200, r.text

    r = student.get("/api/me/curriculum?kind=ezber")
    assert r.json()["categories"][0]["items"][0]["status"] == "ezberlendi"

    r = teacher.get(f"/api/students/{sid}/tracking-summary")
    assert r.json()["ezber"] == {"completed": 1, "total": 1, "pct": 100}
    assert r.json()["badge"] == "Altın Rozet"


def test_list_categories_template_without_student():
    teacher, classroom, student, sid = _class_with_student()
    cat = teacher.post("/api/curriculum/categories", json={"kind": "ezber", "title": "SEVİYE 1"}).json()
    teacher.post(f"/api/curriculum/categories/{cat['id']}/items", json={"title": "Kelime-i Şehadet"})

    r = teacher.get("/api/curriculum/categories?kind=ezber")
    assert r.status_code == 200, r.text
    assert r.json()[0]["items"][0]["title"] == "Kelime-i Şehadet"

    r = student.get("/api/me/page-logs")
    assert r.status_code == 200
    assert r.json() == []


def test_curriculum_invalid_kind_rejected():
    teacher, _ = solo_teacher()
    r = teacher.post("/api/curriculum/categories", json={"kind": "yanlis", "title": "X"})
    assert r.status_code == 422


def test_student_cannot_set_own_status():
    teacher, classroom, student, sid = _class_with_student()
    cat = teacher.post("/api/curriculum/categories", json={"kind": "tecvid", "title": "Mahreçler"}).json()
    item = teacher.post(f"/api/curriculum/categories/{cat['id']}/items", json={"title": "Elif"}).json()
    r = student.post(f"/api/curriculum/items/{item['id']}/status", json={"student_id": sid, "status": "ezberlendi"})
    assert r.status_code == 403


def test_attendance_save_and_summary():
    teacher, classroom, student, sid = _class_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/attendance",
                      json={"date": "2026-09-06", "records": [{"student_id": sid, "status": "geldi"}]})
    assert r.status_code == 200, r.text
    assert r.json()["saved"] == 1

    r = teacher.get(f"/api/classes/{classroom['id']}/attendance?date=2026-09-06")
    assert r.json()[0]["status"] == "geldi"

    # aynı tarihe tekrar kayıt -> güncelleme, çift satır değil
    teacher.post(f"/api/classes/{classroom['id']}/attendance",
                 json={"date": "2026-09-06", "records": [{"student_id": sid, "status": "izinli"}]})
    r = teacher.get(f"/api/classes/{classroom['id']}/attendance/summary")
    assert r.json()[0]["total"] == 1
    assert r.json()[0]["present"] == 0

    r = teacher.get(f"/api/students/{sid}/tracking-summary")
    assert r.json()["attendance"] == {"total": 1, "present": 0, "rate_pct": 0}


def test_page_log_create_list_delete_and_guardian_view():
    teacher, classroom, student, sid = _class_with_student()
    guardian = _guardian_for(teacher, classroom["id"], sid)

    r = teacher.post(f"/api/students/{sid}/page-logs",
                      json={"log_date": "2026-09-06", "start_page": 1, "end_page": 10})
    assert r.status_code == 201, r.text
    log_id = r.json()["id"]

    r = student.get(f"/api/students/{sid}/page-logs")
    assert len(r.json()) == 1

    r = guardian.get(f"/api/students/{sid}/tracking-summary")
    assert r.json()["pages"] == {"current_page": 10, "total_read": 10, "log_count": 1}

    r = teacher.delete(f"/api/students/{sid}/page-logs/{log_id}")
    assert r.status_code == 200, r.text
    assert student.get(f"/api/students/{sid}/page-logs").json() == []


def test_other_teacher_cannot_manage_unrelated_student():
    _, classroom, _, sid = _class_with_student()
    other_teacher, _ = solo_teacher()
    r = other_teacher.get(f"/api/students/{sid}/tracking-summary")
    assert r.status_code == 404
    r = other_teacher.post(f"/api/students/{sid}/page-logs", json={"log_date": "2026-09-06", "start_page": 1, "end_page": 2})
    assert r.status_code == 404
