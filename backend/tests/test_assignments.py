from tests.helpers import create_classroom, join_as_guardian, join_as_student, solo_teacher


def _setup_with_student():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    return teacher, classroom, student


def test_create_assignment_targets_active_students():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments", json={"title": "Bakara 1-5 tilavet"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["target_count"] == 1
    assert body["submitted_count"] == 0
    assert set(body["submission_types"]) == {"audio", "text", "file"}


def test_student_sees_own_assignment_and_submits_text():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Metin ödevi", "submission_types": ["text"]})
    assignment_id = r.json()["id"]

    r = student.get("/api/me/assignments")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["submission"]["status"] == "bekliyor"

    r = student.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "Tamamladım"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "teslim_edildi"
    assert r.json()["text_content"] == "Tamamladım"


def test_submit_rejects_disallowed_type():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Sadece ses", "submission_types": ["audio"]})
    assignment_id = r.json()["id"]
    r = student.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "yazı"})
    assert r.status_code == 422
    assert r.json()["detail"] == "text_not_allowed"


def test_teacher_reviews_submission():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Metin ödevi", "submission_types": ["text"]})
    assignment_id = r.json()["id"]
    student.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "Tamamladım"})

    r = teacher.get(f"/api/assignments/{assignment_id}")
    assert r.status_code == 200
    submission_id = r.json()["submissions"][0]["submission_id"]

    r = teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 4, "feedback_text": "Güzel"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "incelendi"
    assert r.json()["review"]["score"] == 4

    r = student.get(f"/api/me/assignments/{assignment_id}/submission")
    assert r.json()["review"]["score"] == 4


def test_review_before_submit_returns_422():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments", json={"title": "Ödev"})
    assignment_id = r.json()["id"]
    r = teacher.get(f"/api/assignments/{assignment_id}")
    submission_id = r.json()["submissions"][0]["submission_id"]
    r = teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 3})
    assert r.status_code == 422


def test_other_teacher_cannot_view_assignment():
    teacher, classroom, student = _setup_with_student()
    other_teacher, _ = solo_teacher()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments", json={"title": "Ödev"})
    assignment_id = r.json()["id"]
    r = other_teacher.get(f"/api/assignments/{assignment_id}")
    assert r.status_code == 404


def test_guardian_can_view_linked_child_submission():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]})
    assignment_id = r.json()["id"]
    student.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "bitti"})

    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/guardian-invite", json={}).json()
    guardian, _ = join_as_guardian(invite["token"])

    r = teacher.get(f"/api/assignments/{assignment_id}")
    submission_id = r.json()["submissions"][0]["submission_id"]
    r = guardian.get(f"/api/submissions/{submission_id}")
    assert r.status_code == 200
    assert r.json()["text_content"] == "bitti"


def test_unrelated_guardian_cannot_view_submission():
    teacher, classroom, student = _setup_with_student()
    r = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]})
    assignment_id = r.json()["id"]
    student.post(f"/api/me/assignments/{assignment_id}/submit", data={"text_content": "bitti"})

    other_classroom = create_classroom(teacher, "Başka sınıf")
    other_student, _ = join_as_student(other_classroom["join_code"])
    other_student_id = teacher.get(f"/api/classes/{other_classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(
        f"/api/classes/{other_classroom['id']}/students/{other_student_id}/guardian-invite", json={}
    ).json()
    unrelated_guardian, _ = join_as_guardian(invite["token"])

    r = teacher.get(f"/api/assignments/{assignment_id}")
    submission_id = r.json()["submissions"][0]["submission_id"]
    r = unrelated_guardian.get(f"/api/submissions/{submission_id}")
    assert r.status_code == 404
