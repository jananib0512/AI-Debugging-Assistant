from fastapi import FastAPI
from api.routes import router
from auth.middleware import AuthMiddleware
app = FastAPI()
app.add_middleware(AuthMiddleware)
app.include_router(router)
@app.get("/health")
def health():
    return {"status": "ok"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
