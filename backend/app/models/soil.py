from pydantic import BaseModel, Field


class SoilAdvisoryRequest(BaseModel):
    nitrogen: float = Field(..., ge=0, le=300)
    phosphorus: float = Field(..., ge=0, le=300)
    potassium: float = Field(..., ge=0, le=300)

    ph: float = Field(..., ge=0, le=14)
    soil_type: str = Field(..., min_length=2, max_length=100)
    crop: str = Field(..., min_length=2, max_length=100)
    location: str = Field(default="Salem", max_length=100)