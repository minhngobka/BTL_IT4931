from flask import Flask, render_template, request, Response, jsonify
import json
from recommendation.recommender import recommender
import os
import math

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/')
def index():
    """Trang chính"""
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """API lấy gợi ý sản phẩm"""
    data = request.json
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Missing product_id'}), 400
    
    # Lấy gợi ý từ recommender
    recommendations = recommender.get_recommendations(product_id, top_n=5)
    
    return jsonify({
        'product_id': product_id,
        'recommendations': recommendations
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 20))
        
        products_cursor = recommender.db.product_catalog.find().skip(skip).limit(limit)
        total = recommender.db.product_catalog.count_documents({})
        
        products = []
        for doc in products_cursor:
            doc['_id'] = str(doc['_id'])

            # Xử lý NaN nếu có
            for k, v in doc.items():
                if isinstance(v, float) and math.isnan(v):
                    doc[k] = None
            
            products.append(doc)

        return Response(json.dumps({
            'products': products,
            'total': total
        }, default=str), mimetype='application/json')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)