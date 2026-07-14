"""
数据模型定义
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Product:
    """商品数据模型"""
    name: str
    price: float
    platform: str
    url: str
    sales: int = 0
    shop_rating: float = 0.0
    shop_name: str = ""
    image_url: str = ""
    product_id: str = ""
    original_price: float = 0.0
    collected_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SearchResult:
    """搜索结果集合"""
    keyword: str
    products: List[Product] = field(default_factory=list)
    search_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    total_count: int = 0

    def add_product(self, product: Product):
        self.products.append(product)
        self.total_count = len(self.products)

    def to_dict(self) -> dict:
        return {
            'keyword': self.keyword,
            'products': [p.to_dict() for p in self.products],
            'search_time': self.search_time,
            'total_count': self.total_count
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchResult':
        products = [Product.from_dict(p) for p in data.get('products', [])]
        return cls(
            keyword=data.get('keyword', ''),
            products=products,
            search_time=data.get('search_time', ''),
            total_count=len(products)
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'SearchResult':
        return cls.from_dict(json.loads(json_str))
