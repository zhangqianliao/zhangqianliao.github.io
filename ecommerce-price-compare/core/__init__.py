"""
电商商品价格自动化采集与对比工具
核心模块包
"""

from .models import Product, SearchResult
from .scraper import ProductScraper
from .analyzer import PriceAnalyzer

__all__ = ['Product', 'SearchResult', 'ProductScraper', 'PriceAnalyzer']
__version__ = '1.0.0'
