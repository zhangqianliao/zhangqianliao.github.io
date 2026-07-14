"""
Flask 后端服务
提供网页API接口，支持调用爬虫和分析模块
"""

import sys
import os
import json
from flask import Flask, render_template, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import ProductScraper
from core.analyzer import PriceAnalyzer
from core.models import SearchResult

app = Flask(__name__, template_folder='templates', static_folder='static')


def get_sample_data():
    """获取示例数据"""
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'samples', 'sample_data.json'
    )
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


@app.route('/')
def index():
    """首页"""
    sample_data = get_sample_data()
    return render_template('index.html', sample_data=sample_data)


@app.route('/api/search', methods=['GET', 'POST'])
def api_search():
    """搜索API"""
    if request.method == 'POST':
        data = request.get_json() or {}
        keyword = data.get('keyword', '').strip()
        platforms_str = data.get('platforms', '')
        use_mock = data.get('use_mock', True)
        page_size = int(data.get('page_size', 20))
    else:
        keyword = request.args.get('keyword', '').strip()
        platforms_str = request.args.get('platforms', '')
        use_mock = request.args.get('use_mock', 'true').lower() == 'true'
        page_size = int(request.args.get('page_size', 20))

    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400

    platforms = None
    if platforms_str:
        platforms = [p.strip() for p in platforms_str.split(',') if p.strip()]

    try:
        scraper = ProductScraper(platforms=platforms, use_mock=use_mock)
        result = scraper.search_all(keyword, page_size=page_size)

        analyzer = PriceAnalyzer(result.products)
        analysis = analyzer.full_analysis()

        return jsonify({
            'success': True,
            'keyword': keyword,
            'search_time': result.search_time,
            'total_count': result.total_count,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/platforms')
def api_platforms():
    """获取支持的平台列表"""
    platforms = ProductScraper.get_available_platforms()
    return jsonify({
        'platforms': platforms
    })


@app.route('/api/sample')
def api_sample():
    """获取示例数据"""
    sample = get_sample_data()
    if sample:
        return jsonify({
            'success': True,
            'data': sample
        })
    return jsonify({'success': False, 'error': '示例数据不存在'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
