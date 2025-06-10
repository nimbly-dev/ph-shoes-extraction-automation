# extractors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4

@dataclass
class BaseShoe:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    subTitle: Optional[str] = None
    url: str = ""
    image: Optional[str] = None
    price_sale: float = 0.0
    price_original: Optional[float] = None
    gender: str = ""  
    age_group: Optional[str] = "adult"
    brand: str = "unknown"

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> List[BaseShoe]:
        """
        This method should be implemented by each brand-specific extractor.
        It must return a list of Shoe instances.
        """
        pass

class BaseCleaner(ABC):
    @abstractmethod
    def clean(self, data: List[BaseShoe]) -> List[BaseShoe]:
        """
        This method should be implemented by each brand-specific cleaner.
        It must return a cleaned list of Shoe instances.
        """
        pass