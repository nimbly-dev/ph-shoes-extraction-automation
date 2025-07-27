from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4
import pandas as pd  

@dataclass
class BaseShoe:
    id: str                   = field(default_factory=lambda: str(uuid4()))
    title: str                = ""
    subTitle: Optional[str]   = None
    url: str                  = ""
    image: Optional[str]      = None
    price_sale: float         = 0.0
    price_original: Optional[float] = None
    gender: List[str]         = field(default_factory=list)
    age_group: Optional[str]  = "adult"
    brand: str                = "unknown"
    extra: Optional[str]      = None   # JSON-blob of site-specific bits

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> List[BaseShoe]:
        """Return a list of BaseShoe instances."""
        pass

class BaseCleaner(ABC):
    @abstractmethod
    def clean(self, df) -> pd.DataFrame:
        """Takes a DataFrame of raw records, returns cleaned DataFrame."""
        pass
