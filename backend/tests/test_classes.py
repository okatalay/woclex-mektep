from helpers import create_classroom, join_as_student, solo_teacher


def test_teacher_cannot_manage_others_classroom(teacher):
    classroom = create_classroom(teacher)
    other, _ = solo_teacher("individual")
    other_classroom = create_classroom(other)

    r = teacher.get(f"/api/classes/{other_classroom['id']}")
    assert r.status_code == 404

    r2 = teacher.patch(f"/api/classes/{other_classroom['id']}", json={"name": "Ele geçirildi"})
    assert r2.status_code == 404


def test_student_cannot_create_classroom(teacher):
    classroom = create_classroom(teacher)
    student_c, _ = join_as_student(classroom["join_code"])
    r = student_c.post("/api/classes", json={"name": "Kendi sınıfım"})
    assert r.status_code == 403


def test_regenerate_code_changes_code_and_invalidates_old(teacher):
    classroom = create_classroom(teacher)
    old_code = classroom["join_code"]
    r = teacher.post(f"/api/classes/{classroom['id']}/regenerate-code")
    assert r.status_code == 200
    new_code = r.json()["join_code"]
    assert new_code != old_code

    stale = teacher.get(f"/api/auth/join-info/{old_code}")
    assert stale.status_code == 404
    fresh = teacher.get(f"/api/auth/join-info/{new_code}")
    assert fresh.status_code == 200


def test_institution_admin_can_manage_all_classrooms(institution_owner):
    classroom = create_classroom(institution_owner, "Kurum Sınıfı")
    r = institution_owner.get(f"/api/classes/{classroom['id']}")
    assert r.status_code == 200
    listed = institution_owner.get("/api/classes").json()
    assert any(c["id"] == classroom["id"] for c in listed)
