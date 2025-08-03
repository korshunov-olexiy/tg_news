import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="10.7.0.1", port=8000)
