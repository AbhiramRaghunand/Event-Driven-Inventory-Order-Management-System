from fastapi import FastAPI

from app.routes.auth import router as auth_router


app = FastAPI(title="BEA API")
app.include_router(auth_router)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
