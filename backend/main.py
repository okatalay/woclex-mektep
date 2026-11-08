from fastapi import FastAPI

from routers import (
    announcements, assignments, auth, classes, curriculum, dashboard, guardians, library, messages, routes,
    submissions, tracking,
)

app = FastAPI(title="Mektep", docs_url=None, redoc_url=None, openapi_url=None)

for r in (
    auth.router, classes.router, guardians.router, assignments.router, submissions.router,
    dashboard.router, messages.router, announcements.router, routes.router, library.router,
    curriculum.router, tracking.router,
):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"ok": True}
