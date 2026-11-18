"""Rutas API de exportación de datos."""

from fastapi import APIRouter, Depends, Response

from app.db.session import get_db
from app.modules.data_service import EXPORT_FORMAT_VERSION, export_json_payload

router = APIRouter(tags=["export"])


@router.get("/export")
def export_data(db = Depends(get_db)):
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
