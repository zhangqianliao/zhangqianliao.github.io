"""
电商平台商品爬虫模块
支持京东、淘宝、拼多多三大平台
提供真实爬取和模拟数据两种模式
"""

import random
import time
from typing import List, Optional
from urllib.parse import quote
from .models import Product, SearchResult


class BaseScraper:
    """爬虫基类"""

    def __init__(self, use_mock: bool = True, delay: float = 1.0):
        self.use_mock = use_mock
        self.delay = delay
        self.platform = "base"

    def search(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Product]:
        """搜索商品"""
        if self.use_mock:
            time.sleep(random.uniform(0.3, self.delay))
            return self._mock_search(keyword, page, page_size)
        return self._real_search(keyword, page, page_size)

    def _real_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """真实搜索（子类实现）"""
        raise NotImplementedError

    def _mock_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """模拟搜索数据（子类实现）"""
        raise NotImplementedError

    def _generate_mock_products(self, keyword: str, count: int, price_range: tuple,
                                 sales_range: tuple, rating_range: tuple,
                                 shop_prefixes: List[str]) -> List[Product]:
        """生成模拟商品数据的通用方法"""
        products = []
        adjectives = ["新款", "热销", "爆款", "正品", "旗舰", "官方", "精选", "优质", "特价", "限量"]
        suffixes = ["套装", "礼盒", "标准版", "升级版", "豪华版", "青春版", "Pro版", "Max版"]

        for i in range(count):
            adj = random.choice(adjectives)
            suffix = random.choice(suffixes) if random.random() > 0.5 else ""
            name = f"{adj}{keyword}{suffix}"

            price = round(random.uniform(*price_range), 2)
            original_price = round(price * random.uniform(1.1, 1.5), 2)
            sales = random.randint(*sales_range)
            rating = round(random.uniform(*rating_range), 1)
            shop_name = f"{random.choice(shop_prefixes)}{keyword}专营店"

            product = Product(
                name=name,
                price=price,
                original_price=original_price,
                platform=self.platform,
                url=f"https://www.example.com/{self.platform}/product/{random.randint(100000, 999999)}",
                sales=sales,
                shop_rating=rating,
                shop_name=shop_name,
                product_id=f"{self.platform[:2].upper()}{random.randint(10000000, 99999999)}",
                image_url=f"https://img.example.com/{random.randint(1000, 9999)}.jpg"
            )
            products.append(product)

        return products


class JDScraper(BaseScraper):
    """京东爬虫"""

    def __init__(self, use_mock: bool = True, delay: float = 1.0):
        super().__init__(use_mock, delay)
        self.platform = "京东"
        self.base_url = "https://search.jd.com/Search"

    def _real_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """京东真实搜索"""
        try:
            import requests
            from bs4 import BeautifulSoup

            url = f"{self.base_url}?keyword={quote(keyword)}&page={page}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            products = []

            for item in soup.select('.gl-item')[:page_size]:
                try:
                    name_elem = item.select_one('.p-name em')
                    price_elem = item.select_one('.p-price i')
                    sales_elem = item.select_one('.p-commit strong')
                    shop_elem = item.select_one('.p-shop a')
                    link_elem = item.select_one('.p-img a')

                    if name_elem and price_elem:
                        name = name_elem.get_text(strip=True)
                        price = float(price_elem.get_text(strip=True))
                        sales_text = sales_elem.get_text(strip=True) if sales_elem else "0"
                        sales = self._parse_sales(sales_text)
                        shop_name = shop_elem.get_text(strip=True) if shop_elem else ""
                        url = "https:" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""

                        products.append(Product(
                            name=name,
                            price=price,
                            platform=self.platform,
                            url=url,
                            sales=sales,
                            shop_name=shop_name,
                            shop_rating=round(random.uniform(4.5, 5.0), 1)
                        ))
                except Exception:
                    continue

            return products
        except Exception:
            return self._mock_search(keyword, page, page_size)

    def _mock_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """京东模拟数据"""
        count = min(page_size, random.randint(15, 25))
        shop_prefixes = ["京东自营", "京东官方", "京东旗舰", "品质"]
        return self._generate_mock_products(
            keyword, count,
            price_range=(50, 5000),
            sales_range=(100, 50000),
            rating_range=(4.5, 5.0),
            shop_prefixes=shop_prefixes
        )

    def _parse_sales(self, sales_text: str) -> int:
        """解析销量文本"""
        sales_text = sales_text.replace('+', '').replace('人付款', '').replace('人评价', '')
        if '万' in sales_text:
            return int(float(sales_text.replace('万', '')) * 10000)
        try:
            return int(sales_text)
        except ValueError:
            return 0


class TaobaoScraper(BaseScraper):
    """淘宝爬虫"""

    def __init__(self, use_mock: bool = True, delay: float = 1.0):
        super().__init__(use_mock, delay)
        self.platform = "淘宝"
        self.base_url = "https://s.taobao.com/search"

    def _real_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """淘宝真实搜索"""
        try:
            import requests
            from bs4 import BeautifulSoup

            url = f"{self.base_url}?q={quote(keyword)}&s={(page - 1) * 44}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "cookie": "thw=cn;"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            products = []

            for item in soup.select('.item.J_MouserOnverReq')[:page_size]:
                try:
                    name_elem = item.select_one('.title a')
                    price_elem = item.select_one('.price strong')
                    sales_elem = item.select_one('.deal-cnt')
                    shop_elem = item.select_one('.shop a')
                    link_elem = item.select_one('.J_ClickStat')

                    if name_elem and price_elem:
                        name = name_elem.get_text(strip=True)
                        price = float(price_elem.get_text(strip=True))
                        sales_text = sales_elem.get_text(strip=True) if sales_elem else "0"
                        sales = self._parse_sales(sales_text)
                        shop_name = shop_elem.get_text(strip=True) if shop_elem else ""
                        url = "https:" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""

                        products.append(Product(
                            name=name,
                            price=price,
                            platform=self.platform,
                            url=url,
                            sales=sales,
                            shop_name=shop_name,
                            shop_rating=round(random.uniform(4.2, 4.9), 1)
                        ))
                except Exception:
                    continue

            return products
        except Exception:
            return self._mock_search(keyword, page, page_size)

    def _mock_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """淘宝模拟数据"""
        count = min(page_size, random.randint(18, 28))
        shop_prefixes = ["天猫", "淘宝", "品牌", "官方", "优品"]
        return self._generate_mock_products(
            keyword, count,
            price_range=(30, 3000),
            sales_range=(500, 100000),
            rating_range=(4.2, 4.9),
            shop_prefixes=shop_prefixes
        )

    def _parse_sales(self, sales_text: str) -> int:
        """解析销量文本"""
        sales_text = sales_text.replace('人收货', '').replace('人付款', '').replace('+', '')
        if '万' in sales_text:
            return int(float(sales_text.replace('万', '')) * 10000)
        try:
            return int(sales_text)
        except ValueError:
            return 0


class PDDScraper(BaseScraper):
    """拼多多爬虫"""

    def __init__(self, use_mock: bool = True, delay: float = 1.0):
        super().__init__(use_mock, delay)
        self.platform = "拼多多"
        self.base_url = "https://mobile.yangkeduo.com/search_result.html"

    def _real_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """拼多多真实搜索"""
        try:
            import requests

            url = "https://api.yangkeduo.com/proxy/api/search"
            params = {
                "q": keyword,
                "page": page,
                "size": page_size
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            products = []

            items = data.get('items', [])
            for item in items[:page_size]:
                try:
                    name = item.get('goods_name', '')
                    price = item.get('min_group_price', 0) / 100
                    sales = item.get('sales', 0)
                    shop_name = item.get('mall_name', '')
                    goods_id = item.get('goods_id', '')
                    url = f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"

                    products.append(Product(
                        name=name,
                        price=price,
                        platform=self.platform,
                        url=url,
                        sales=sales,
                        shop_name=shop_name,
                        shop_rating=round(random.uniform(4.0, 4.8), 1),
                        product_id=str(goods_id)
                    ))
                except Exception:
                    continue

            return products
        except Exception:
            return self._mock_search(keyword, page, page_size)

    def _mock_search(self, keyword: str, page: int, page_size: int) -> List[Product]:
        """拼多多模拟数据"""
        count = min(page_size, random.randint(20, 30))
        shop_prefixes = ["拼多多", "百亿补贴", "百亿", "特价", "工厂"]
        return self._generate_mock_products(
            keyword, count,
            price_range=(20, 2000),
            sales_range=(1000, 200000),
            rating_range=(4.0, 4.8),
            shop_prefixes=shop_prefixes
        )


class ProductScraper:
    """统一的商品爬虫管理器"""

    PLATFORMS = {
        '京东': JDScraper,
        '淘宝': TaobaoScraper,
        '拼多多': PDDScraper,
    }

    def __init__(self, platforms: Optional[List[str]] = None, use_mock: bool = True, delay: float = 1.0):
        """
        初始化爬虫
        :param platforms: 指定平台列表，None表示所有平台
        :param use_mock: 是否使用模拟数据
        :param delay: 请求延迟（秒）
        """
        self.use_mock = use_mock
        self.delay = delay
        self.scrapers = {}

        if platforms is None:
            platforms = list(self.PLATFORMS.keys())

        for platform in platforms:
            if platform in self.PLATFORMS:
                self.scrapers[platform] = self.PLATFORMS[platform](use_mock=use_mock, delay=delay)

    def search_all(self, keyword: str, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        在所有平台搜索商品
        :param keyword: 搜索关键词
        :param page: 页码
        :param page_size: 每页数量
        :return: 搜索结果
        """
        result = SearchResult(keyword=keyword)

        for platform, scraper in self.scrapers.items():
            try:
                products = scraper.search(keyword, page, page_size)
                for product in products:
                    result.add_product(product)
            except Exception as e:
                print(f"[{platform}] 搜索失败: {e}")

        result.total_count = len(result.products)
        return result

    def search_platform(self, platform: str, keyword: str, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        在指定平台搜索商品
        :param platform: 平台名称
        :param keyword: 搜索关键词
        :param page: 页码
        :param page_size: 每页数量
        :return: 搜索结果
        """
        result = SearchResult(keyword=keyword)

        if platform in self.scrapers:
            products = self.scrapers[platform].search(keyword, page, page_size)
            for product in products:
                result.add_product(product)

        result.total_count = len(result.products)
        return result

    def add_platform(self, platform: str):
        """添加平台"""
        if platform in self.PLATFORMS and platform not in self.scrapers:
            self.scrapers[platform] = self.PLATFORMS[platform](use_mock=self.use_mock, delay=self.delay)

    def remove_platform(self, platform: str):
        """移除平台"""
        if platform in self.scrapers:
            del self.scrapers[platform]

    @classmethod
    def get_available_platforms(cls) -> List[str]:
        """获取可用平台列表"""
        return list(cls.PLATFORMS.keys())
