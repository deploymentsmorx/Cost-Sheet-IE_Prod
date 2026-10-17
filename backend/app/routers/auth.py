from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class WebLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


async def _auth_request(method: str, path: str, **kwargs) -> httpx.Response:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            return await client.request(
                method,
                f"{settings.auth_api_url.rstrip('/')}{path}",
                **kwargs,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="The sign-in service is temporarily unavailable. Please try again.",
        ) from exc


def _raise_upstream_error(response: httpx.Response) -> None:
    try:
        detail = response.json().get("detail", "Sign-in failed.")
    except ValueError:
        detail = "Sign-in failed."
    raise HTTPException(status_code=response.status_code, detail=detail)


@router.post("/login")
async def login(body: WebLoginRequest):
    response = await _auth_request(
        "POST",
        "/api/auth/login",
        json={"username": body.email.strip(), "password": body.password, "product_code": "costsheet"},
    )
    if response.status_code != 200:
        _raise_upstream_error(response)
    return response.json()


@router.get("/me")
def me(request: Request):
    return request.state.costsheet_user


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, request: Request):
    token = request.headers.get("authorization", "")
    response = await _auth_request(
        "POST",
        "/api/auth/change-password",
        json={"current_password": body.current_password, "new_password": body.new_password},
        headers={"Authorization": token},
    )
    if response.status_code != 200:
        _raise_upstream_error(response)
    return response.json()
