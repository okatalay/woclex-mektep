from conftest import PW, new_client, register_teacher, uname
from helpers import create_classroom, join_as_guardian, join_as_student


def test_register_teacher_individual_creates_org(client):
    me = register_teacher(client, "individual")
    assert me["organization"]["type"] == "individual"
    assert me["role"]["system_key"] == "owner"
    assert "classroom.create" in me["permissions"]


def test_register_teacher_institution_requires_name(client):
    r = client.post("/api/auth/register", json={
        "account_type": "institution", "username": uname(), "password": PW, "full_name": "Kurum Sahibi",
    })
    assert r.status_code == 422


def test_login_and_me(teacher):
    me = teacher.get("/api/auth/me").json()
    assert me["role"]["system_key"] == "owner"


def test_login_wrong_password_fails():
    c = new_client()
    u = uname()
    register_teacher(c, "individual", username=u)
    c2 = new_client()
    r = c2.post("/api/auth/login", json={"username": u, "password": "wrong-pass"})
    assert r.status_code == 401


def test_join_with_code(teacher):
    classroom = create_classroom(teacher)
    info = teacher.get(f"/api/auth/join-info/{classroom['join_code']}")
    assert info.status_code == 200
    assert info.json()["classroom_name"] == classroom["name"]

    student_c, me = join_as_student(classroom["join_code"])
    assert me["role"]["system_key"] == "student"
    assert me["organization"]["id"] == teacher.get("/api/auth/me").json()["organization"]["id"]


def test_join_with_invalid_code_404(client):
    r = client.post("/api/auth/register-student", json={
        "join_code": "NOPE-NOPE", "username": uname(), "password": PW, "full_name": "Xx",
    })
    assert r.status_code == 404


def test_join_disabled_code_404(teacher):
    classroom = create_classroom(teacher)
    r = teacher.patch(f"/api/classes/{classroom['id']}", json={"join_enabled": False})
    assert r.status_code == 200
    r2 = teacher.post("/api/auth/register-student", json={
        "join_code": classroom["join_code"], "username": uname(), "password": PW, "full_name": "Xx",
    })
    assert r2.status_code == 404


def test_guardian_invite_flow(teacher):
    classroom = create_classroom(teacher)
    _, student_me = join_as_student(classroom["join_code"])
    students = teacher.get(f"/api/classes/{classroom['id']}/students").json()
    assert len(students) == 1
    student_id = students[0]["student_id"]

    inv = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/guardian-invite",
                        json={"relation": "anne"})
    assert inv.status_code == 201
    token = inv.json()["token"]

    preview = teacher.get(f"/api/auth/guardian-invite/{token}")
    assert preview.status_code == 200
    assert preview.json()["student_name"] == "Test Öğrenci"

    guardian_c, guardian_me = join_as_guardian(token)
    assert guardian_me["role"]["system_key"] == "guardian"

    # Token tek kullanımlık: ikinci kez kullanılamaz
    r2 = guardian_c.post("/api/auth/register-guardian", json={
        "token": token, "username": uname(), "password": PW, "full_name": "İkinci Veli",
    })
    assert r2.status_code == 404
