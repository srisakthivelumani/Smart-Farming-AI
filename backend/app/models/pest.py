from pydantic import BaseModel, Field


class PestAdvisoryRequest(BaseModel):
    crop: str = Field(..., min_length=2, max_length=100)
    symptoms: str = Field(..., min_length=5, max_length=2000)
    affected_part: str = Field(..., min_length=2, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    location: str = Field(default="Salem", max_length=100)

    