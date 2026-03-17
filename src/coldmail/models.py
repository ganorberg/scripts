from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Lead:
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    title: Optional[str] = None
    company_size: Optional[str] = None
    source: Optional[str] = None
    campaign_id: Optional[str] = None
    verified_status: str = "unverified"
    uploaded_to_instantly: bool = False
    id: Optional[int] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company_name": self.company_name,
            "title": self.title,
            "company_size": self.company_size,
            "source": self.source,
            "campaign_id": self.campaign_id,
            "verified_status": self.verified_status,
            "uploaded_to_instantly": int(self.uploaded_to_instantly),
        }
