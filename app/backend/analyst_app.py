"""
Analyst Dashboard Application
Hiển thị kết quả phân tích batch: Funnel, Segments, Churn, Trends
"""

from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGODB_DATABASE', 'bigdata_db')

app = Flask(__name__, 
            template_folder='../templates/analyst',
            static_folder='../static')

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]


# ============== PAGES ==============

@app.route('/')
def dashboard():
    """Trang chính - Overview Dashboard"""
    return render_template('dashboard.html')


@app.route('/funnel')
def funnel_page():
    """Trang Funnel Analysis"""
    return render_template('funnel.html')


@app.route('/segments')
def segments_page():
    """Trang Customer Segments"""
    return render_template('segments.html')


@app.route('/churn')
def churn_page():
    """Trang Churn Prediction"""
    return render_template('churn.html')


@app.route('/trends')
def trends_page():
    """Trang Time Series Trends"""
    return render_template('trends.html')


# ============== APIs ==============

@app.route('/api/overview')
def api_overview():
    """API tổng quan - số liệu chính"""
    try:
        # Đếm số documents trong các collections
        total_events = db.customer_events.count_documents({})
        total_users = db.user_feature_engineering.count_documents({})
        total_products = db.product_catalog.count_documents({})
        total_segments = db.customer_segments.count_documents({})
        
        # Lấy funnel mới nhất
        funnel = list(db.journey_metrics.find({}, {'_id': 0}).sort('analysis_timestamp', -1).limit(8))
        
        return jsonify({
            'success': True,
            'overview': {
                'total_events': total_events,
                'total_users': total_users,
                'total_products': total_products,
                'total_segments': total_segments
            },
            'funnel': funnel
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/funnel')
def api_funnel():
    """API Funnel Metrics"""
    try:
        metrics = list(db.journey_metrics.find(
            {}, {'_id': 0}
        ).sort('analysis_timestamp', -1).limit(8))
        
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/segments')
def api_segments():
    """API Customer Segments"""
    try:
        # Aggregate by segment
        pipeline = [
            {'$group': {
                '_id': '$segment_name',
                'count': {'$sum': 1},
                'total_revenue': {'$sum': '$total_spent'},
                'avg_spent': {'$avg': '$total_spent'},
                'avg_purchases': {'$avg': '$purchase_count'},
                'avg_value_score': {'$avg': '$customer_value_score'}
            }},
            {'$sort': {'avg_spent': -1}}
        ]
        segments = list(db.customer_segments.aggregate(pipeline))
        
        # Top users per segment
        top_users = list(db.customer_segments.find(
            {}, {'_id': 0, 'user_id': 1, 'segment_name': 1, 'total_spent': 1, 'purchase_count': 1}
        ).sort('total_spent', -1).limit(20))
        
        return jsonify({
            'success': True,
            'segments': segments,
            'top_users': top_users
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/churn')
def api_churn():
    """API Churn Predictions"""
    try:
        # High risk users (predicted to churn)
        high_risk = list(db.churn_predictions.find(
            {'churn_prediction': 1},
            {'_id': 0}
        ).sort('total_spent', -1).limit(50))
        
        # Stats
        total = db.churn_predictions.count_documents({})
        churned = db.churn_predictions.count_documents({'churn_prediction': 1})
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total,
                'predicted_churn': churned,
                'churn_rate': round(churned / total * 100, 2) if total > 0 else 0
            },
            'high_risk_users': high_risk
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/trends')
def api_trends():
    """API Time Series Trends"""
    try:
        # Get daily trends
        trends = list(db.time_series_analysis.find(
            {},
            {'_id': 0, 'date': 1, 'event_type': 1, 'event_count': 1, 
             'unique_users': 1, 'revenue': 1, 'ma_7day_events': 1, 'day_over_day_growth': 1}
        ).sort('date', -1).limit(100))
        
        return jsonify({'success': True, 'trends': trends})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/user/<user_id>')
def api_user_detail(user_id):
    """API User 360° Profile"""
    try:
        uid = int(user_id)
        
        features = db.user_feature_engineering.find_one({'user_id': uid}, {'_id': 0})
        segment = db.customer_segments.find_one({'user_id': uid}, {'_id': 0})
        churn = db.churn_predictions.find_one({'user_id': uid}, {'_id': 0})
        
        return jsonify({
            'success': True,
            'user_id': uid,
            'features': features,
            'segment': segment,
            'churn': churn
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("🚀 Starting Analyst Dashboard...")
    print("📊 Dashboard: http://localhost:5001")
    print("📈 Funnel:    http://localhost:5001/funnel")
    print("👥 Segments:  http://localhost:5001/segments")
    print("⚠️  Churn:     http://localhost:5001/churn")
    app.run(debug=True, port=5001)  # Port 5001 để không conflict với app.py