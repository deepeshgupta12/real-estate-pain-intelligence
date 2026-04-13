"""Organization management API."""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.organization import Organization

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrgCreateRequest(BaseModel):
    slug: str
    name: str
    plan: str = "free"
    owner_email: str | None = None
    max_runs_per_month: int = 10


class OrgResponse(BaseModel):
    id: int
    slug: str
    name: str
    plan: str
    is_active: bool
    max_runs_per_month: int
    api_key: str | None
    created_at: str
    owner_email: str | None

    model_config = {"from_attributes": True}


@router.post("", response_model=OrgResponse, status_code=201)
def create_organization(payload: OrgCreateRequest, db: Session = Depends(get_db)) -> Organization:
    existing = db.query(Organization).filter(Organization.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Organization slug '{payload.slug}' already exists")

    org = Organization(
        slug=payload.slug,
        name=payload.name,
        plan=payload.plan,
        owner_email=payload.owner_email,
        max_runs_per_month=payload.max_runs_per_month,
        api_key=secrets.token_urlsafe(32),
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{slug}", response_model=OrgResponse)
def get_organization(slug: str, db: Session = Depends(get_db)) -> Organization:
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{slug}' not found")
    return org


@router.post("/{slug}/rotate-api-key", response_model=OrgResponse)
def rotate_api_key(slug: str, db: Session = Depends(get_db)) -> Organization:
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{slug}' not found")
    org.api_key = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(org)
    return org


@router.get("")
def list_organizations(db: Session = Depends(get_db)) -> list[dict]:
    orgs = db.query(Organization).all()
    return [{"id": o.id, "slug": o.slug, "name": o.name, "plan": o.plan, "is_active": o.is_active} for o in orgs]
