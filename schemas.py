from typing import Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    text: str
    page_no: Optional[int] = None


class EquityIncentiveExtract(BaseModel):

    doc_id: str

    company_name: str

    stock_code: Optional[str] = None

    grant_amount: float = Field(
        description="拟授予总数量（万份）"
    )

    grant_ratio: Optional[float] = Field(
        description="占总股本比例（%）"
    )

    participant_count: int = Field(
        description="首次授予总人数"
    )

    exercise_price: float = Field(
        description="行权价格（元/份）"
    )

    discount_rate: Optional[float] = Field(
    default=None,
    description="定价折扣率（%）"
)

    waiting_period: Optional[float] = Field(
        default=None,
        description="等待期（月）"
    )

    validity_period: Optional[float]= Field(
        description="激励计划最长有效期（月）"
    )

    evidences: list[Evidence]