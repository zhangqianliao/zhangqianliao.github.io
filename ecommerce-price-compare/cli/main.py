"""
命令行工具入口
"""

import sys
import os
import argparse
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import ProductScraper
from core.analyzer import PriceAnalyzer
from core.models import SearchResult


def print_table(products, sort_by="price", max_rows=20):
    """以表格形式打印商品列表"""
    if not products:
        print("没有找到商品")
        return

    headers = ["排名", "平台", "商品名称", "价格(元)", "销量", "店铺评分", "店铺名称"]
    col_widths = [6, 8, 40, 10, 10, 10, 20]

    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    separator = "-+-".join("-" * w for w in col_widths)

    print(f"\n{'=' * len(header_line)}")
    print(f"  共找到 {len(products)} 个商品（显示前 {min(max_rows, len(products))} 个）")
    print(f"{'=' * len(header_line)}")
    print(header_line)
    print(separator)

    for i, p in enumerate(products[:max_rows], 1):
        name = p.name[:38] + "..." if len(p.name) > 38 else p.name
        shop = p.shop_name[:18] + "..." if len(p.shop_name) > 18 else p.shop_name
        sales_str = format_sales(p.sales)

        row = [
            str(i).ljust(6),
            p.platform.ljust(8),
            name.ljust(40),
            f"{p.price:.2f}".rjust(10),
            sales_str.rjust(10),
            f"{p.shop_rating:.1f}".rjust(10),
            shop.ljust(20)
        ]
        print(" | ".join(row))

    print(f"{'-' * len(header_line)}\n")


def format_sales(sales: int) -> str:
    """格式化销量显示"""
    if sales >= 10000:
        return f"{sales / 10000:.1f}万"
    return str(sales)


def print_price_stats(stats: dict):
    """打印价格统计"""
    print("\n" + "=" * 50)
    print("  价格统计")
    print("=" * 50)
    print(f"  商品数量: {stats.get('count', 0)}")
    print(f"  最低价:   ¥{stats.get('min', 0):.2f}")
    print(f"  最高价:   ¥{stats.get('max', 0):.2f}")
    print(f"  平均价:   ¥{stats.get('avg', 0):.2f}")
    print(f"  中位数:   ¥{stats.get('median', 0):.2f}")
    print(f"  价格区间: ¥{stats.get('range', 0):.2f}")
    print("=" * 50)


def print_platform_stats(stats: dict):
    """打印平台统计"""
    print("\n" + "=" * 70)
    print("  各平台对比")
    print("=" * 70)
    print(f"  {'平台':<8} {'数量':<6} {'最低价':<10} {'最高价':<10} {'平均价':<10} {'平均评分':<10}")
    print("  " + "-" * 66)

    for platform, data in stats.items():
        print(f"  {platform:<8} {data['count']:<6} "
              f"¥{data['min_price']:<9.2f} ¥{data['max_price']:<9.2f} "
              f"¥{data['avg_price']:<9.2f} {data['avg_rating']:<10.2f}")

    print("=" * 70)


def print_recommendations(recommendations: list):
    """打印性价比推荐"""
    print("\n" + "=" * 70)
    print("  🏆 性价比 TOP 5 推荐")
    print("=" * 70)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, item in enumerate(recommendations[:5]):
        p = item['product']
        medal = medals[i] if i < len(medals) else f"  {i + 1}."
        name = p.name[:35] + "..." if len(p.name) > 35 else p.name
        print(f"  {medal} 评分: {item['score']:.1f}分 | {p.platform} | ¥{p.price:.2f}")
        print(f"      {name}")
        print(f"      销量: {format_sales(p.sales)} | 评分: {p.shop_rating:.1f} | {p.shop_name}")
        if i < len(recommendations[:5]) - 1:
            print("  " + "-" * 66)

    print("=" * 70)


def print_comparison(comparison: dict):
    """打印对比结论"""
    print("\n" + "=" * 60)
    print("  📊 横向对比结论")
    print("=" * 60)
    print(f"  {comparison.get('conclusion', '')}")

    if comparison.get('cheapest_platform'):
        print(f"  • 最实惠平台: {comparison['cheapest_platform']}")
    if comparison.get('highest_rating_platform'):
        print(f"  • 最高评分平台: {comparison['highest_rating_platform']}")
    if comparison.get('most_products_platform'):
        print(f"  • 商品最多平台: {comparison['most_products_platform']}")

    print("=" * 60)


def cmd_search(args):
    """搜索命令"""
    keyword = args.keyword
    platforms = args.platforms.split(',') if args.platforms else None
    use_mock = not args.real
    page_size = args.limit

    print(f"\n🔍 正在搜索: {keyword}")
    if use_mock:
        print("   模式: 模拟数据（演示用）")
    else:
        print("   模式: 真实爬取")
    if platforms:
        print(f"   平台: {', '.join(platforms)}")
    print()

    scraper = ProductScraper(platforms=platforms, use_mock=use_mock)
    result = scraper.search_all(keyword, page_size=page_size)

    analyzer = PriceAnalyzer(result.products)
    analysis = analyzer.full_analysis()

    sort_map = {
        'price': 'price',
        'sales': 'sales',
        'rating': 'rating',
        'value': 'value'
    }
    sort_by = sort_map.get(args.sort, 'price')

    if sort_by == 'price':
        analyzer.sort_by_price(ascending=True)
    elif sort_by == 'sales':
        analyzer.sort_by_sales(ascending=False)
    elif sort_by == 'rating':
        analyzer.sort_by_rating(ascending=False)
    elif sort_by == 'value':
        analyzer.sort_by_value(ascending=False)

    print_table(analyzer.products, sort_by=sort_by)
    print_price_stats(analysis['price_stats'])
    print_platform_stats(analysis['platform_stats'])
    print_comparison(analysis['comparison'])
    print_recommendations(analysis['value_recommendations'])

    if args.output:
        output_data = {
            'keyword': keyword,
            'search_time': result.search_time,
            'analysis': analysis
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {args.output}")


def cmd_platforms(args):
    """显示支持的平台"""
    platforms = ProductScraper.get_available_platforms()
    print("\n📋 支持的电商平台:")
    for i, p in enumerate(platforms, 1):
        print(f"  {i}. {p}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='电商商品价格自动化采集与对比工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli/main.py search "蓝牙耳机"          # 搜索蓝牙耳机（模拟数据）
  python cli/main.py search "手机" --real       # 真实爬取手机商品
  python cli/main.py search "笔记本" --platforms 京东,淘宝  # 指定平台
  python cli/main.py search "键盘" --sort sales   # 按销量排序
  python cli/main.py search "鼠标" --output result.json  # 保存结果
  python cli/main.py platforms                  # 查看支持的平台
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    search_parser = subparsers.add_parser('search', help='搜索商品并对比价格')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--platforms', '-p', default=None,
                               help='指定平台，逗号分隔（如：京东,淘宝,拼多多）')
    search_parser.add_argument('--limit', '-n', type=int, default=20,
                               help='每个平台返回的商品数量（默认20）')
    search_parser.add_argument('--sort', '-s', default='price',
                               choices=['price', 'sales', 'rating', 'value'],
                               help='排序方式：price/sales/rating/value（默认price）')
    search_parser.add_argument('--real', action='store_true',
                               help='使用真实爬取模式（需要网络，可能被反爬）')
    search_parser.add_argument('--output', '-o', default=None,
                               help='将结果保存为JSON文件')

    subparsers.add_parser('platforms', help='查看支持的平台列表')

    args = parser.parse_args()

    if args.command == 'search':
        cmd_search(args)
    elif args.command == 'platforms':
        cmd_platforms(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
