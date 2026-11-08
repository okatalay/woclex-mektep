from tests.helpers import create_classroom, join_as_student, solo_teacher


def _setup_route_with_two_stops():
    teacher, _ = solo_teacher()
    classroom = create_classroom(teacher)
    student, _ = join_as_student(classroom["join_code"])
    route = teacher.post(f"/api/classes/{classroom['id']}/routes",
                          json={"title": "Tecvid Rotası", "description": "Adım adım tecvid"}).json()
    stop1 = teacher.post(f"/api/routes/{route['id']}/stops",
                          json={"title": "Tecvid Bul 01", "submission_types": ["text"]}).json()
    stop2 = teacher.post(f"/api/routes/{route['id']}/stops",
                          json={"title": "Tecvid Haritası 01", "submission_types": ["text"]}).json()
    return teacher, classroom, student, route, stop1, stop2


def test_create_route_and_stops_orders_sequentially():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    assert stop1["order_index"] == 0
    assert stop2["order_index"] == 1
    assert stop1["target_count"] == 1

    r = teacher.get(f"/api/routes/{route['id']}")
    assert r.status_code == 200
    assert len(r.json()["stops"]) == 2


def test_student_sees_first_stop_unlocked_second_locked():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    r = student.get(f"/api/me/routes/{route['id']}")
    assert r.status_code == 200
    stops = r.json()["stops"]
    assert stops[0]["locked"] is False
    assert stops[0]["status"] == "bekliyor"
    assert stops[1]["locked"] is True


def test_second_stop_unlocks_after_first_reviewed():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    student.post(f"/api/me/assignments/{stop1['assignment_id']}/submit", data={"text_content": "tamam"})

    r = student.get(f"/api/me/routes/{route['id']}")
    assert r.json()["stops"][1]["locked"] is True

    submission_id = teacher.get(f"/api/assignments/{stop1['assignment_id']}").json()["submissions"][0]["submission_id"]
    teacher.post(f"/api/submissions/{submission_id}/review", json={"score": 5})

    r = student.get(f"/api/me/routes/{route['id']}")
    body = r.json()
    assert body["stops"][1]["locked"] is False
    assert body["completed_count"] == 1
    assert body["progress_pct"] == 50


def test_my_routes_lists_progress_summary():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    r = student.get("/api/me/routes")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["stop_count"] == 2
    assert r.json()[0]["completed_count"] == 0


def test_other_teacher_cannot_manage_route():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    other_teacher, _ = solo_teacher()
    r = other_teacher.get(f"/api/routes/{route['id']}")
    assert r.status_code == 404
    r = other_teacher.post(f"/api/routes/{route['id']}/stops", json={"title": "Xx"})
    assert r.status_code == 404


def test_student_not_in_classroom_cannot_view_route():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    other_classroom = create_classroom(teacher, "Başka sınıf")
    outsider, _ = join_as_student(other_classroom["join_code"])
    r = outsider.get(f"/api/me/routes/{route['id']}")
    assert r.status_code == 404


def test_teacher_can_update_stop_title_and_types():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    r = teacher.patch(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}",
                       json={"title": "Tecvid Bul 01 (güncel)", "submission_types": ["audio"]})
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Tecvid Bul 01 (güncel)"
    assert r.json()["submission_types"] == ["audio"]

    r = teacher.get(f"/api/routes/{route['id']}")
    assert r.json()["stops"][0]["title"] == "Tecvid Bul 01 (güncel)"


def test_teacher_can_delete_stop_and_reindexes_remaining():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    stop3 = teacher.post(f"/api/routes/{route['id']}/stops",
                          json={"title": "Tecvid Testi 01", "submission_types": ["text"]}).json()

    r = teacher.delete(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}")
    assert r.status_code == 200, r.text

    r = teacher.get(f"/api/routes/{route['id']}")
    stops = r.json()["stops"]
    assert [s["title"] for s in stops] == ["Tecvid Haritası 01", "Tecvid Testi 01"]
    assert [s["order_index"] for s in stops] == [0, 1]

    # silinen duraktaki ödev de kalkmış olmalı
    r = teacher.get(f"/api/assignments/{stop1['assignment_id']}")
    assert r.status_code == 404


def test_deleting_first_stop_unlocks_new_first_for_student():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    teacher.delete(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}")

    r = student.get(f"/api/me/routes/{route['id']}")
    stops = r.json()["stops"]
    assert len(stops) == 1
    assert stops[0]["locked"] is False


def test_teacher_can_move_stop_up_and_down():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    r = teacher.post(f"/api/routes/{route['id']}/stops/{stop2['stop_id']}/move", json={"direction": "up"})
    assert r.status_code == 200, r.text

    r = teacher.get(f"/api/routes/{route['id']}")
    stops = r.json()["stops"]
    assert stops[0]["title"] == "Tecvid Haritası 01"
    assert stops[1]["title"] == "Tecvid Bul 01"


def test_move_beyond_bounds_returns_422():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    r = teacher.post(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}/move", json={"direction": "up"})
    assert r.status_code == 422


def test_other_teacher_cannot_update_or_delete_stop():
    teacher, classroom, student, route, stop1, stop2 = _setup_route_with_two_stops()
    other_teacher, _ = solo_teacher()
    r = other_teacher.patch(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}", json={"title": "Xx"})
    assert r.status_code == 404
    r = other_teacher.delete(f"/api/routes/{route['id']}/stops/{stop1['stop_id']}")
    assert r.status_code == 404
