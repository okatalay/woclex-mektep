from helpers import create_classroom, join_as_guardian, join_as_student, solo_teacher


def _invite_guardian(teacher, classroom_id, student_id, relation="anne"):
    r = teacher.post(f"/api/classes/{classroom_id}/students/{student_id}/guardian-invite", json={"relation": relation})
    assert r.status_code == 201, r.text
    return r.json()["token"]


def test_student_detail_includes_guardians(teacher):
    classroom = create_classroom(teacher)
    _, student_me = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]

    detail = teacher.get(f"/api/classes/{classroom['id']}/students/{student_id}")
    assert detail.status_code == 200
    assert detail.json()["guardians"] == []

    token = _invite_guardian(teacher, classroom["id"], student_id)
    join_as_guardian(token)

    detail2 = teacher.get(f"/api/classes/{classroom['id']}/students/{student_id}")
    guardians = detail2.json()["guardians"]
    assert len(guardians) == 1
    assert guardians[0]["relation"] == "anne"


def test_other_teacher_cannot_see_student_detail(teacher):
    classroom = create_classroom(teacher)
    _, student_me = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]

    other, _ = solo_teacher("individual")
    r = other.get(f"/api/classes/{classroom['id']}/students/{student_id}")
    assert r.status_code == 404


def test_remove_student_hides_from_list(teacher):
    classroom = create_classroom(teacher)
    _, student_me = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]

    r = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/remove")
    assert r.status_code == 200

    students = teacher.get(f"/api/classes/{classroom['id']}/students").json()
    assert students == []

    detail = teacher.get(f"/api/classes/{classroom['id']}/students/{student_id}")
    assert detail.status_code == 404


def test_guardian_sees_linked_children_with_classrooms(teacher):
    classroom = create_classroom(teacher, "Hafızlık Sınıfı")
    _, student_me = join_as_student(classroom["join_code"], full_name="Zehra Yılmaz")
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]

    token = _invite_guardian(teacher, classroom["id"], student_id, relation="baba")
    guardian_c, _ = join_as_guardian(token)

    children = guardian_c.get("/api/guardians/me/children").json()
    assert len(children) == 1
    assert children[0]["full_name"] == "Zehra Yılmaz"
    assert children[0]["relation"] == "baba"
    assert children[0]["classrooms"][0]["name"] == "Hafızlık Sınıfı"


def test_guardian_with_no_children_sees_empty_list(teacher):
    classroom = create_classroom(teacher)
    _, student_me = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    token = _invite_guardian(teacher, classroom["id"], student_id)
    guardian_c, _ = join_as_guardian(token)

    # Farklı bir öğrenciye bağlı olmayan ikinci bir veli hiçbir çocuk görmemeli.
    classroom2 = create_classroom(teacher, "Başka Sınıf")
    _, _ = join_as_student(classroom2["join_code"])

    children = guardian_c.get("/api/guardians/me/children").json()
    assert len(children) == 1  # yalnızca kendi bağlı olduğu çocuk
