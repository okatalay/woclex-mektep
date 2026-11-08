from conftest import PW, new_client, register_teacher, uname


def create_classroom(c, name="Hafızlık Sınıfı"):
    r = c.post("/api/classes", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def join_as_student(join_code, username=None, full_name="Test Öğrenci"):
    c = new_client()
    u = username or uname("s")
    r = c.post("/api/auth/register-student", json={
        "join_code": join_code, "username": u, "password": PW, "full_name": full_name,
    })
    assert r.status_code == 201, r.text
    return c, r.json()


def join_as_guardian(token, username=None, full_name="Test Veli"):
    c = new_client()
    u = username or uname("v")
    r = c.post("/api/auth/register-guardian", json={
        "token": token, "username": u, "password": PW, "full_name": full_name,
    })
    assert r.status_code == 201, r.text
    return c, r.json()


def solo_teacher(account_type="individual"):
    c = new_client()
    me = register_teacher(c, account_type)
    return c, me["username"]
