
from fastapi import APIRouter, Query

from app.services.mandi_service import MandiPriceService

router = APIRouter(prefix="/mandi-prices", tags=["Mandi Prices"])

service = MandiPriceService()


@router.get("")
async def get_mandi_prices(
    commodity: str = Query(default="", max_length=100),
    state: str = Query(default="", max_length=100),
    district: str = Query(default="", max_length=100),
):
    return await service.get_prices(
        commodity=commodity,
        state=state,
        district=district,
    )
