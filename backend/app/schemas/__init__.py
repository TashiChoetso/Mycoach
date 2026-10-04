from datetime import date as Date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    timezone: str = Field(default="UTC", max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=400)
    password: str = Field(min_length=10, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class PreferencesOut(APIModel):
    theme: str
    week_starts_on: int
    scoring_weights: dict
    dashboard_sections: list


class SelectedAreaOut(APIModel):
    id: str
    area_id: str
    name: str
    slug: str | None
    is_custom: bool
    is_enabled: bool
    dashboard_visible: bool
    sort_order: int
    icon: str | None = None


class CatalogAreaOut(APIModel):
    id: str
    slug: str | None
    name: str
    icon: str | None
    selected: bool


class UserOut(APIModel):
    id: str
    email: str
    display_name: str
    timezone: str
    locale: str
    currency: str
    onboarding_completed_at: str | None
    preferences: PreferencesOut | None = None
    areas: list[SelectedAreaOut] = []


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    currency: str | None = Field(default=None, max_length=8)


class PreferencesUpdate(BaseModel):
    theme: str | None = None
    week_starts_on: int | None = Field(default=None, ge=0, le=6)
    scoring_weights: dict[str, float] | None = None
    dashboard_sections: list[str] | None = None


class AreaCreate(BaseModel):
    area_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class AreaUpdate(BaseModel):
    custom_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_enabled: bool | None = None
    dashboard_visible: bool | None = None
    sort_order: int | None = None


class AreasResponse(BaseModel):
    catalog: list[CatalogAreaOut]
    selected: list[SelectedAreaOut]


class FocusCreate(BaseModel):
    user_area_id: str
    name: str = Field(min_length=1, max_length=120)
    prompt: str | None = Field(default=None, max_length=400)
    kind: str = "check"
    target_value: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=32)


class FocusUpdate(BaseModel):
    custom_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_enabled: bool | None = None
    sort_order: int | None = None


class FocusLogRequest(BaseModel):
    date: Date | None = None
    value: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=400)


class PriorityUpdate(BaseModel):
    period: str
    text: str = Field(default="", max_length=400)


class TodayDashboard(BaseModel):
    greeting: dict
    momentum: dict
    week: list[dict] = []
    week_days: list[dict] = []
    tasks: dict
    habits: dict
    finance: dict | None
    areas: list[dict]
    coach: dict | None
    date: str | None = None
    priorities: dict = {}


TokenResponse.model_rebuild()
