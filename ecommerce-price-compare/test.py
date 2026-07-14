"""
测试脚本 - 验证核心功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scraper import ProductScraper
from core.analyzer import PriceAnalyzer
from core.models import Product, SearchResult


def test_models():
    """测试数据模型"""
    print("=" * 50)
    print("测试 1: 数据模型")
    print("=" * 50)

    p = Product(
        name="测试商品",
        price=99.99,
        platform="测试平台",
        url="https://example.com",
        sales=1000,
        shop_rating=4.8,
        shop_name="测试店铺"
    )

    assert p.name == "测试商品"
    assert p.price == 99.99
    assert p.platform == "测试平台"

    d = p.to_dict()
    assert d['name'] == "测试商品"
    assert d['price'] == 99.99

    p2 = Product.from_dict(d)
    assert p2.name == p.name
    assert p2.price == p.price

    result = SearchResult(keyword="测试")
    result.add_product(p)
    assert result.total_count == 1

    json_str = result.to_json()
    result2 = SearchResult.from_json(json_str)
    assert result2.keyword == "测试"
    assert len(result2.products) == 1

    print("✅ 数据模型测试通过")
    print()


def test_scraper():
    """测试爬虫模块"""
    print("=" * 50)
    print("测试 2: 爬虫模块（模拟数据模式）")
    print("=" * 50)

    platforms = ProductScraper.get_available_platforms()
    print(f"支持的平台: {platforms}")
    assert len(platforms) >= 3

    scraper = ProductScraper(use_mock=True)
    result = scraper.search_all("蓝牙耳机", page_size=5)

    print(f"搜索关键词: {result.keyword}")
    print(f"找到商品数: {result.total_count}")
    assert result.total_count > 0

    for p in result.products[:3]:
        print(f"  - [{p.platform}] {p.name[:30]}... ¥{p.price}")

    print("✅ 爬虫模块测试通过")
    print()
    return result


def test_analyzer(result):
    """测试分析模块"""
    print("=" * 50)
    print("测试 3: 数据分析模块")
    print("=" * 50)

    analyzer = PriceAnalyzer(result.products)

    cleaned = analyzer.clean_data()
    print(f"清洗后商品数: {len(cleaned)}")
    assert len(cleaned) > 0

    deduped = analyzer.deduplicate()
    print(f"去重后商品数: {len(deduped)}")

    analyzer.sort_by_price(ascending=True)
    print(f"价格排序后第一个: ¥{analyzer.products[0].price}")
    assert analyzer.products[0].price <= analyzer.products[-1].price

    price_stats = analyzer.get_price_stats()
    print(f"价格统计: 最低¥{price_stats['min']} 最高¥{price_stats['max']} 平均¥{price_stats['avg']}")
    assert 'count' in price_stats
    assert 'min' in price_stats
    assert 'max' in price_stats
    assert 'avg' in price_stats

    platform_stats = analyzer.get_platform_stats()
    print(f"平台统计: {list(platform_stats.keys())}")
    assert len(platform_stats) > 0

    distribution = analyzer.get_price_distribution()
    print(f"价格分布区间数: {len(distribution['bins'])}")
    assert 'bins' in distribution
    assert 'counts' in distribution

    recommendations = analyzer.get_value_recommendations(top_n=5)
    print(f"性价比推荐数: {len(recommendations)}")
    assert len(recommendations) > 0
    for rec in recommendations[:3]:
        print(f"  第{rec['rank']}名: 评分{rec['score']}分 - {rec['product'].name[:20]}")

    comparison = analyzer.compare_by_platform()
    print(f"最实惠平台: {comparison['cheapest_platform']}")
    print(f"对比结论: {comparison['conclusion']}")

    full_result = analyzer.full_analysis()
    assert 'products' in full_result
    assert 'price_stats' in full_result
    assert 'platform_stats' in full_result
    assert 'comparison' in full_result
    assert 'value_recommendations' in full_result

    print("✅ 数据分析模块测试通过")
    print()


def test_single_platform():
    """测试单平台搜索"""
    print("=" * 50)
    print("测试 4: 单平台搜索")
    print("=" * 50)

    scraper = ProductScraper(platforms=['京东'], use_mock=True)
    result = scraper.search_platform('京东', '手机', page_size=3)

    print(f"京东搜索结果: {result.total_count} 个商品")
    for p in result.products:
        assert p.platform == "京东"
        print(f"  - {p.name[:30]}... ¥{p.price}")

    print("✅ 单平台搜索测试通过")
    print()


def main():
    print("\n" + "🚀" * 20)
    print("  电商价格对比工具 - 功能测试")
    print("🚀" * 20 + "\n")

    try:
        test_models()

        result = test_scraper()

        test_analyzer(result)

        test_single_platform()

        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        print()
        print("使用方法:")
        print("  命令行模式: python run.py search \"关键词\"")
        print("  网页模式:   python run.py web")
        print("  查看帮助:   python run.py --help")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
