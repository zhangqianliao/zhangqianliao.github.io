"""
数据分析模块
包含数据清洗、去重、排序、价格对比、性价比分析等功能
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from difflib import SequenceMatcher
from .models import Product, SearchResult


class PriceAnalyzer:
    """价格分析器"""

    def __init__(self, products: Optional[List[Product]] = None):
        self.products = products or []

    def load_products(self, products: List[Product]):
        """加载商品列表"""
        self.products = products

    def load_from_search_result(self, result: SearchResult):
        """从搜索结果加载"""
        self.products = result.products

    # ========== 数据清洗 ==========

    def clean_data(self) -> List[Product]:
        """数据清洗：移除无效数据、格式化字段"""
        cleaned = []
        seen_ids = set()

        for p in self.products:
            if not p.name or p.price <= 0:
                continue

            if p.product_id and p.product_id in seen_ids:
                continue
            if p.product_id:
                seen_ids.add(p.product_id)

            p.name = self._clean_text(p.name)
            p.shop_name = self._clean_text(p.shop_name)
            p.price = round(float(p.price), 2)
            p.sales = max(0, int(p.sales))
            p.shop_rating = min(5.0, max(0.0, float(p.shop_rating)))

            cleaned.append(p)

        self.products = cleaned
        return cleaned

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    # ========== 去重 ==========

    def deduplicate(self, threshold: float = 0.85) -> List[Product]:
        """
        商品去重
        :param threshold: 相似度阈值，0-1之间
        """
        if len(self.products) < 2:
            return self.products

        unique_products = []
        used_indices = set()

        for i, p1 in enumerate(self.products):
            if i in used_indices:
                continue

            best_product = p1
            used_indices.add(i)

            for j, p2 in enumerate(self.products[i + 1:], start=i + 1):
                if j in used_indices:
                    continue

                similarity = self._name_similarity(p1.name, p2.name)

                if similarity >= threshold and p1.platform == p2.platform:
                    used_indices.add(j)
                    if p2.price < best_product.price:
                        best_product = p2

            unique_products.append(best_product)

        self.products = unique_products
        return unique_products

    def _name_similarity(self, name1: str, name2: str) -> float:
        """计算商品名称相似度"""
        name1_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', name2.lower())

        if not name1_clean or not name2_clean:
            return 0.0

        return SequenceMatcher(None, name1_clean, name2_clean).ratio()

    # ========== 排序 ==========

    def sort_by_price(self, ascending: bool = True) -> List[Product]:
        """按价格排序"""
        self.products.sort(key=lambda p: p.price, reverse=not ascending)
        return self.products

    def sort_by_sales(self, ascending: bool = False) -> List[Product]:
        """按销量排序"""
        self.products.sort(key=lambda p: p.sales, reverse=not ascending)
        return self.products

    def sort_by_rating(self, ascending: bool = False) -> List[Product]:
        """按店铺评分排序"""
        self.products.sort(key=lambda p: p.shop_rating, reverse=not ascending)
        return self.products

    def sort_by_value(self, ascending: bool = False) -> List[Product]:
        """按性价比评分排序"""
        scored = self._calculate_value_scores()
        self.products.sort(key=lambda p: scored.get(p.product_id or p.name, 0), reverse=not ascending)
        return self.products

    # ========== 统计分析 ==========

    def get_price_stats(self) -> Dict:
        """获取价格统计信息"""
        if not self.products:
            return {}

        prices = [p.price for p in self.products]
        prices_sorted = sorted(prices)
        n = len(prices)

        return {
            'count': n,
            'min': min(prices),
            'max': max(prices),
            'avg': round(sum(prices) / n, 2),
            'median': round(prices_sorted[n // 2] if n % 2 else (prices_sorted[n // 2 - 1] + prices_sorted[n // 2]) / 2, 2),
            'range': round(max(prices) - min(prices), 2)
        }

    def get_platform_stats(self) -> Dict[str, Dict]:
        """按平台统计"""
        platform_data = defaultdict(list)

        for p in self.products:
            platform_data[p.platform].append(p)

        stats = {}
        for platform, products in platform_data.items():
            prices = [p.price for p in products]
            stats[platform] = {
                'count': len(products),
                'min_price': min(prices) if prices else 0,
                'max_price': max(prices) if prices else 0,
                'avg_price': round(sum(prices) / len(prices), 2) if prices else 0,
                'total_sales': sum(p.sales for p in products),
                'avg_rating': round(sum(p.shop_rating for p in products) / len(products), 2) if products else 0
            }

        return stats

    # ========== 性价比分析 ==========

    def _calculate_value_scores(self) -> Dict[str, float]:
        """计算性价比评分"""
        if not self.products:
            return {}

        prices = [p.price for p in self.products]
        sales = [p.sales for p in self.products]
        ratings = [p.shop_rating for p in self.products]

        min_price, max_price = min(prices), max(prices)
        max_sales = max(sales) if sales else 1
        max_rating = max(ratings) if ratings else 5.0

        scores = {}
        for p in self.products:
            price_score = 1 - (p.price - min_price) / (max_price - min_price + 1e-9)
            sales_score = p.sales / max_sales if max_sales > 0 else 0
            rating_score = p.shop_rating / max_rating if max_rating > 0 else 0

            value_score = price_score * 0.4 + sales_score * 0.35 + rating_score * 0.25
            key = p.product_id or p.name
            scores[key] = round(value_score * 100, 2)

        return scores

    def get_value_recommendations(self, top_n: int = 5) -> List[Dict]:
        """获取性价比推荐"""
        scores = self._calculate_value_scores()

        scored_products = []
        for p in self.products:
            key = p.product_id or p.name
            scored_products.append({
                'product': p,
                'score': scores.get(key, 0),
                'rank': 0
            })

        scored_products.sort(key=lambda x: x['score'], reverse=True)

        for i, item in enumerate(scored_products):
            item['rank'] = i + 1

        return scored_products[:top_n]

    # ========== 横向对比 ==========

    def compare_by_platform(self) -> Dict:
        """各平台横向对比"""
        platform_stats = self.get_platform_stats()
        price_stats = self.get_price_stats()

        cheapest_platform = None
        highest_rating_platform = None
        most_products_platform = None

        min_avg_price = float('inf')
        max_avg_rating = 0
        max_count = 0

        for platform, stats in platform_stats.items():
            if stats['avg_price'] < min_avg_price:
                min_avg_price = stats['avg_price']
                cheapest_platform = platform
            if stats['avg_rating'] > max_avg_rating:
                max_avg_rating = stats['avg_rating']
                highest_rating_platform = platform
            if stats['count'] > max_count:
                max_count = stats['count']
                most_products_platform = platform

        return {
            'platform_stats': platform_stats,
            'overall_stats': price_stats,
            'cheapest_platform': cheapest_platform,
            'highest_rating_platform': highest_rating_platform,
            'most_products_platform': most_products_platform,
            'conclusion': self._generate_comparison_conclusion(
                cheapest_platform, highest_rating_platform, most_products_platform, price_stats
            )
        }

    def _generate_comparison_conclusion(self, cheapest, highest_rating, most_products, price_stats) -> str:
        """生成对比结论"""
        parts = []
        if cheapest:
            parts.append(f"{cheapest}平均价格最低")
        if highest_rating:
            parts.append(f"{highest_rating}店铺评分最高")
        if most_products:
            parts.append(f"{most_products}商品数量最多")

        if price_stats:
            parts.append(f"价格区间 {price_stats.get('min', 0):.2f} - {price_stats.get('max', 0):.2f} 元")

        return "；".join(parts) + "。"

    # ========== 价格分布 ==========

    def get_price_distribution(self, bins: int = 10) -> Dict:
        """获取价格分布"""
        if not self.products:
            return {'bins': [], 'counts': []}

        prices = [p.price for p in self.products]
        min_p, max_p = min(prices), max(prices)

        if min_p == max_p:
            return {
                'bins': [f"{min_p:.2f}"],
                'counts': [len(prices)],
                'min': min_p,
                'max': max_p
            }

        bin_size = (max_p - min_p) / bins
        counts = [0] * bins
        bin_labels = []

        for i in range(bins):
            start = min_p + i * bin_size
            end = min_p + (i + 1) * bin_size
            bin_labels.append(f"{start:.0f}-{end:.0f}")

        for price in prices:
            idx = min(int((price - min_p) / bin_size), bins - 1)
            counts[idx] += 1

        return {
            'bins': bin_labels,
            'counts': counts,
            'min': min_p,
            'max': max_p
        }

    # ========== 完整分析流程 ==========

    def full_analysis(self, dedup_threshold: float = 0.85) -> Dict:
        """执行完整分析流程"""
        self.clean_data()
        self.deduplicate(threshold=dedup_threshold)
        self.sort_by_price(ascending=True)

        return {
            'products': [p.to_dict() for p in self.products],
            'price_stats': self.get_price_stats(),
            'platform_stats': self.get_platform_stats(),
            'comparison': self.compare_by_platform(),
            'price_distribution': self.get_price_distribution(),
            'value_recommendations': [
                {
                    'rank': item['rank'],
                    'score': item['score'],
                    'product': item['product'].to_dict()
                }
                for item in self.get_value_recommendations(top_n=5)
            ]
        }
