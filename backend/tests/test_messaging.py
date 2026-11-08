from tests.helpers import create_classroom, join_as_guardian, join_as_student, solo_teacher


def _setup_with_student_and_guardian():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    student_id = teacher.get(f"/api/classes/{classroom['id']}/students").json()[0]["student_id"]
    invite = teacher.post(f"/api/classes/{classroom['id']}/students/{student_id}/guardian-invite", json={}).json()
    guardian, _ = join_as_guardian(invite["token"])
    return teacher, classroom, student, student_id, guardian


def test_teacher_contacts_include_students_and_guardians():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    r = teacher.get("/api/messages/contacts")
    assert r.status_code == 200
    roles = {c["role"] for c in r.json()}
    assert roles == {"student", "guardian"}


def test_student_contacts_list_teacher():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    r = student.get("/api/messages/contacts")
    assert len(r.json()) == 1
    assert r.json()[0]["role"] == "teacher"


def test_teacher_and_student_can_message_each_other():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    r = teacher.post("/api/messages/conversations", json={"peer_user_id": student_id})
    assert r.status_code == 201, r.text
    conv_id = r.json()["conversation_id"]

    r = teacher.post(f"/api/messages/conversations/{conv_id}/messages", json={"body": "Merhaba, ödevini teslim eder misin?"})
    assert r.status_code == 201, r.text

    r = student.get(f"/api/messages/conversations/{conv_id}/messages")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["body"] == "Merhaba, ödevini teslim eder misin?"
    assert r.json()[0]["mine"] is False

    r = student.post(f"/api/messages/conversations/{conv_id}/messages", json={"body": "Tamam hocam"})
    assert r.status_code == 201

    r = teacher.get("/api/messages/conversations")
    convs = r.json()
    assert len(convs) == 1
    assert convs[0]["last_message"] == "Tamam hocam"


def test_starting_conversation_twice_reuses_same_thread():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    r1 = teacher.post("/api/messages/conversations", json={"peer_user_id": student_id})
    r2 = teacher.post("/api/messages/conversations", json={"peer_user_id": student_id})
    assert r1.json()["conversation_id"] == r2.json()["conversation_id"]


def test_unrelated_teacher_cannot_message_student():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    other_teacher, _ = solo_teacher()
    r = other_teacher.post("/api/messages/conversations", json={"peer_user_id": student_id})
    assert r.status_code == 404


def test_unread_count_tracks_new_messages():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    conv_id = teacher.post("/api/messages/conversations", json={"peer_user_id": student_id}).json()["conversation_id"]
    teacher.post(f"/api/messages/conversations/{conv_id}/messages", json={"body": "selam"})

    r = student.get("/api/messages/unread-count")
    assert r.json()["unread_count"] == 1

    student.get(f"/api/messages/conversations/{conv_id}/messages")
    r = student.get("/api/messages/unread-count")
    assert r.json()["unread_count"] == 0


def test_outsider_cannot_read_conversation():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    conv_id = teacher.post("/api/messages/conversations", json={"peer_user_id": student_id}).json()["conversation_id"]
    r = guardian.get(f"/api/messages/conversations/{conv_id}/messages")
    assert r.status_code == 404


def test_teacher_creates_announcement_and_student_guardian_see_it():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    r = teacher.post(f"/api/classes/{classroom['id']}/announcements", json={"body": "Cumartesi ders saat 10'da."})
    assert r.status_code == 201, r.text

    r = student.get("/api/me/announcements")
    assert len(r.json()) == 1
    assert r.json()[0]["body"] == "Cumartesi ders saat 10'da."

    r = guardian.get("/api/me/announcements")
    assert len(r.json()) == 1
    assert r.json()[0]["classroom_name"] == classroom["name"]


def test_other_classroom_student_does_not_see_announcement():
    teacher, classroom, student, student_id, guardian = _setup_with_student_and_guardian()
    other_classroom = create_classroom(teacher, "Başka sınıf")
    other_student, _ = join_as_student(other_classroom["join_code"])
    teacher.post(f"/api/classes/{classroom['id']}/announcements", json={"body": "Sadece bu sınıfa."})

    r = other_student.get("/api/me/announcements")
    assert r.json() == []
