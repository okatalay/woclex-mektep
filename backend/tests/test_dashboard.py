from tests.helpers import create_classroom, join_as_guardian, join_as_student, solo_teacher


def test_teacher_dashboard_counts_pending_reviews():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a['id']}/submit", data={"text_content": "bitti"})

    r = teacher.get("/api/dashboard")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "teacher"
    assert body["classes_count"] == 1
    assert body["students_count"] == 1
    assert body["pending_review_count"] == 1
    assert body["recent_pending"][0]["student_name"] == "Test Öğrenci"


def test_student_dashboard_progress_and_pending():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a1 = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                       json={"title": "Ödev 1", "submission_types": ["text"]}).json()
    a2 = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                       json={"title": "Ödev 2", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a1['id']}/submit", data={"text_content": "bitti"})

    r = student.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "student"
    assert body["progress"]["assigned"] == 2
    assert body["progress"]["submitted"] == 1
    assert len(body["pending_assignments"]) == 1
    assert body["pending_assignments"][0]["title"] == "Ödev 2"


def test_reviewed_submission_reflects_in_progress_and_avg_score():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a['id']}/submit", data={"text_content": "bitti"})
    submission_id = teacher.get(f"/api/assignments/{a['id']}").json()["submissions"][0]["submission_id"]
    teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 5})

    r = student.get("/api/dashboard")
    progress = r.json()["progress"]
    assert progress["reviewed"] == 1
    assert progress["avg_score"] == 5
    assert progress["completion_rate"] == 100


def test_guardian_dashboard_lists_children_progress():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a['id']}/submit", data={"text_content": "bitti"})

    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/guardian-invite", json={}).json()
    guardian, _ = join_as_guardian(invite["token"])

    r = guardian.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "guardian"
    assert body["children_count"] == 1
    assert body["children"][0]["progress"]["submitted"] == 1


def test_guardian_can_see_child_assignment_history():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a['id']}/submit", data={"text_content": "bitti"})

    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/guardian-invite", json={}).json()
    guardian, _ = join_as_guardian(invite["token"])

    r = guardian.get(f"/api/guardians/children/{student_id}/assignments")
    assert r.status_code == 200
    assert r.json()[0]["title"] == "Ödev"
    assert r.json()[0]["status"] == "teslim_edildi"


def test_unrelated_guardian_cannot_see_child_assignment_history():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]

    other_classroom = create_classroom(teacher, "Başka sınıf")
    other_student, _ = join_as_student(other_classroom["join_code"])
    other_student_id = teacher.get(f"/api/classes/{other_classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(
        f"/api/classes/{other_classroom['id']}/students/{other_student_id}/guardian-invite", json={}
    ).json()
    unrelated_guardian, _ = join_as_guardian(invite["token"])

    r = unrelated_guardian.get(f"/api/guardians/children/{student_id}/assignments")
    assert r.status_code == 404


def test_student_detail_includes_progress():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    a = teacher.post(f"/api/classes/{classroom['id']}/assignments",
                      json={"title": "Ödev", "submission_types": ["text"]}).json()
    student.post(f"/api/me/assignments/{a['id']}/submit", data={"text_content": "bitti"})

    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    r = teacher.get(f"/api/classes/{classroom['id']}/students/{student_id}")
    assert r.json()["progress"]["submitted"] == 1
