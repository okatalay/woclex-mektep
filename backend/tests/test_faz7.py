import io

from tests.helpers import create_classroom, join_as_student, solo_teacher


def _class_with_two_students():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    s1, _ = join_as_student(classroom["join_code"], full_name="Öğrenci Bir")
    s2, _ = join_as_student(classroom["join_code"], full_name="Öğrenci İki")
    return teacher, classroom, s1, s2


def _student_id(teacher, classroom_id, client_full_name):
    r = teacher.get(f"/api/classes/{classroom_id}/students")
    return next(s["student_id"] for s in r.json() if s["full_name"] == client_full_name)


def test_assignment_can_target_specific_students():
    teacher, classroom, s1, s2 = _class_with_two_students()
    sid1 = _student_id(teacher, classroom["id"], "Öğrenci Bir")

    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Sadece bir", "student_ids": [sid1]})
    assert r.status_code == 201, r.text
    assert r.json()["target_count"] == 1

    assert len(s1.get("/api/me/assignments").json()) == 1
    assert len(s2.get("/api/me/assignments").json()) == 0


def test_assignment_attachment_upload_and_download():
    teacher, classroom, s1, _ = _class_with_two_students()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments", json={"title": "Materyalli ödev"})
    assignment_id = r.json()["id"]

    r = teacher.post(f"/api/assignments/{assignment_id}/attachments",
                      files={"files": ("ornek.mp3", io.BytesIO(b"ses-verisi"), "audio/mpeg")})
    assert r.status_code == 201, r.text
    att = r.json()[0]
    assert att["kind"] == "audio"

    r = s1.get(f"/api/me/assignments/{assignment_id}")
    assert r.json()["attachments"][0]["id"] == att["id"]

    r = s1.get(att["url"])
    assert r.status_code == 200
    assert r.content == b"ses-verisi"


def test_review_history_keeps_all_past_feedback():
    teacher, classroom, s1, _ = _class_with_two_students()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Tekrar tekrar", "submission_types": ["text"]})
    assignment_id = r.json()["id"]
    s1.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "ilk"})

    submission_id = teacher.get(f"/api/assignments/{assignment_id}").json()["submissions"][0]["submission_id"]
    teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 2, "feedback_text": "tekrar et", "request_redo": True})

    s1.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "ikinci"})
    teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 5, "feedback_text": "harika"})

    r = s1.get(f"/api/me/assignments/{assignment_id}/submission")
    reviews = r.json()["reviews"]
    assert len(reviews) == 2
    assert reviews[0]["feedback_text"] == "tekrar et"
    assert reviews[1]["feedback_text"] == "harika"
    assert r.json()["review"]["feedback_text"] == "harika"


def test_student_can_delete_own_file_before_review():
    teacher, classroom, s1, _ = _class_with_two_students()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments", json={"title": "Ses ödevi"})
    assignment_id = r.json()["id"]
    r = s1.post(f"/api/me/assignments/{assignment_id}/submit",
                files={"files": ("k.webm", io.BytesIO(b"ses"), "audio/webm")})
    file_id = r.json()["files"][0]["id"]

    r = s1.delete(f"/api/me/assignments/{assignment_id}/files/{file_id}")
    assert r.status_code == 200, r.text
    assert r.json()["files"] == []

    r = s1.post(f"/api/me/assignments/{assignment_id}/submit",
                files={"files": ("k2.webm", io.BytesIO(b"ses2"), "audio/webm")})
    file_id2 = r.json()["files"][-1]["id"]
    submission_id = teacher.get(f"/api/assignments/{assignment_id}").json()["submissions"][0]["submission_id"]
    teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 5})

    r = s1.delete(f"/api/me/assignments/{assignment_id}/files/{file_id2}")
    assert r.status_code == 422


def test_library_item_assign_creates_assignment_with_files():
    teacher, classroom, s1, s2 = _class_with_two_students()
    r = teacher.post("/api/library", json={"kind": "tilavet", "title": "Bakara 1-5"})
    item_id = r.json()["id"]
    r = teacher.post(f"/api/library/{item_id}/files",
                      files={"files": ("ornek.mp3", io.BytesIO(b"ornek-ses"), "audio/mpeg")})
    assert r.status_code == 201, r.text

    sid1 = _student_id(teacher, classroom["id"], "Öğrenci Bir")
    r = teacher.post(f"/api/library/{item_id}/assign", json={"classroom_id": classroom["id"], "student_ids": [sid1]})
    assert r.status_code == 201, r.text
    assignment_id = r.json()["assignment_id"]
    assert r.json()["target_count"] == 1

    r = s1.get(f"/api/me/assignments/{assignment_id}")
    assert r.status_code == 200
    assert len(r.json()["attachments"]) == 1
    assert s2.get(f"/api/me/assignments/{assignment_id}").status_code == 404


def test_route_template_apply_creates_route_with_stops():
    teacher, classroom, s1, s2 = _class_with_two_students()
    r = teacher.post("/api/route-templates", json={"title": "Tecvid yolu"})
    template_id = r.json()["id"]
    teacher.post(f"/api/route-templates/{template_id}/stops", json={"title": "Durak 1"})
    teacher.post(f"/api/route-templates/{template_id}/stops", json={"title": "Durak 2"})

    sid1 = _student_id(teacher, classroom["id"], "Öğrenci Bir")
    r = teacher.post(f"/api/route-templates/{template_id}/apply",
                      json={"classroom_id": classroom["id"], "student_ids": [sid1]})
    assert r.status_code == 201, r.text
    assert r.json()["stop_count"] == 2
    route_id = r.json()["route_id"]

    r = s1.get(f"/api/me/routes/{route_id}")
    assert r.status_code == 200
    assert len(r.json()["stops"]) == 2
    assert s2.get(f"/api/me/routes/{route_id}").status_code == 404


def test_route_can_target_specific_students():
    teacher, classroom, s1, s2 = _class_with_two_students()
    sid1 = _student_id(teacher, classroom["id"], "Öğrenci Bir")
    r = teacher.post(f"/api/classes/{classroom['id']}/routes", json={"title": "Rota", "student_ids": [sid1]})
    assert r.status_code == 201, r.text
    assert r.json()["audience"] == "students"
    route_id = r.json()["id"]
    teacher.post(f"/api/routes/{route_id}/stops", json={"title": "Durak"})

    assert len(s1.get("/api/me/routes").json()) == 1
    assert len(s2.get("/api/me/routes").json()) == 0


def test_archive_files_copy_into_assignment_and_survive_deletion():
    teacher, classroom, s1, s2 = _class_with_two_students()
    item_id = teacher.post("/api/library", json={"kind": "arsiv", "title": "Harf kartı"}).json()["id"]
    teacher.post(f"/api/library/{item_id}/files", files={"files": ("kart.png", io.BytesIO(b"png"), "image/png")})
    assert [i["id"] for i in teacher.get("/api/library?kind=arsiv").json()] == [item_id]
    assert teacher.get("/api/library?kind=tilavet").json() == []

    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    r = teacher.post(f"/api/assignments/{a['id']}/attachments/from-archive", json={"item_ids": [item_id]})
    assert r.status_code == 201, r.text
    att = r.json()[0]
    assert teacher.get(att["url"]).content == b"png"

    # ödev materyalini silmek arşivdeki dosyayı etkilememeli
    teacher.delete(f"/api/assignments/{a['id']}/attachments/{att['id']}")
    files = teacher.get(f"/api/library/{item_id}").json()["files"]
    assert teacher.get(files[0]["url"]).content == b"png"

    t_id = teacher.post("/api/library", json={"kind": "tilavet", "title": "Tilavet"}).json()["id"]
    r = teacher.post(f"/api/library/{t_id}/files/from-archive", json={"item_ids": [item_id]})
    assert r.status_code == 201 and len(r.json()) == 1
    assert teacher.post(f"/api/library/{t_id}/files/from-archive",
                         json={"item_ids": ["00000000-0000-0000-0000-000000000000"]}).status_code == 404
