from fastapi import Header

@router.get("/profile")
def profile(authorization: str = Header(None)):
    return {
        "message": "Welcome! You are an authenticated user.",
        "token": authorization
    }