"""Rutas API de exportación e importación de datos."""

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.db.session import get_db
from app.modules.data_service import EXPORT_FORMAT_VERSION, export_json_payload, import_json_payload

router = APIRouter(tags=["export"])


class ImportRequest(BaseModel):
    payload: str


@router.get("/export")
def export_data(db=Depends(get_db)):
    """Descarga exportación JSON versionada con todas las entidades y relaciones."""
    payload = export_json_payload(db)
    return Response(
        content=payload,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="lifeos-export.json"',
            "X-LifeOS-Format-Version": str(EXPORT_FORMAT_VERSION),
        },
    )


@router.post("/import", status_code=status.HTTP_200_OK)
def import_data(request: ImportRequest, db=Depends(get_db)):
    """Importa un JSON de exportación (merge no destructivo, idempotente por PK)."""
    result = import_json_payload(db, request.payload)
    return result