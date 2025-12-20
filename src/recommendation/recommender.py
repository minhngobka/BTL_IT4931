from pymongo import MongoClient
from collections import defaultdict
import os
from dotenv import load_dotenv
import random

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGODB_DATABASE', 'ecommerce')

class ProductRecommender:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.load_products()
    
    def load_products(self):
        """Load tất cả sản phẩm vào memory"""
        print("Loading products...")
        try:
            self.all_products = list(self.db.product_catalog.find())
            print(f"✅ Loaded {len(self.all_products)} products")
        except Exception as e:
            print(f"⚠️ Could not load products: {e}")
            self.all_products = []
    
    def get_recommendations(self, product_id, top_n=6):
        """
        Lấy gợi ý sản phẩm dựa trên Brand hoặc Category
        
        Chiến lược:
        1. Tìm sản phẩm hiện tại
        2. Gợi ý 5 sản phẩm cùng category/brand
        3. Nếu không đủ, lấy sản phẩm phổ biến nhất
        """
        
        # Tìm sản phẩm hiện tại
        current_product = None
        for p in self.all_products:
            if str(p['product_id']) == str(product_id):
                current_product = p
                break
        
        if not current_product:
            # Nếu không tìm thấy, trả về top products
            return self._get_random_products(top_n)
        
        # Lấy category/brand của sản phẩm hiện tại
        category = current_product.get('category_name', '')
        brand = current_product.get('brand', '')
        
        # Tìm sản phẩm cùng category (ưu tiên cao)
        same_category = [
            p for p in self.all_products 
            if p.get('category_name') == category and str(p['product_id']) != str(product_id)
        ]
        
        # Tìm sản phẩm cùng brand (ưu tiên trung)
        same_brand = [
            p for p in self.all_products 
            if p.get('brand') == brand and str(p['product_id']) != str(product_id)
        ]
        
        # Kết hợp: Category > Brand > Random
        recommendations = []
        
        # Thêm sản phẩm cùng category
        for p in same_category[:3]:  # 3 sản phẩm cùng category
            recommendations.append({
                'product_id': p['product_id'],
                'product_name': p.get('product_name', 'Unknown'),
                'category_name': p.get('category_name', ''),
                'brand': p.get('brand', ''),
                'price': p.get('price', 0),
                'image_url': p.get('image_url', ''),
                'reason': f"Cùng category: {category}",
                'confidence': 0.85
            })
        
        # Thêm sản phẩm cùng brand
        for p in same_brand[:2]:  # 2 sản phẩm cùng brand
            if len(recommendations) < top_n and str(p['product_id']) != str(product_id):
                recommendations.append({
                    'product_id': p['product_id'],
                    'product_name': p.get('product_name', 'Unknown'),
                    'category_name': p.get('category_name', ''),
                    'brand': p.get('brand', ''),
                    'price': p.get('price', 0),
                    'image_url': p.get('image_url', ''),
                    'reason': f"Cùng brand: {brand}",
                    'confidence': 0.70
                })
        
        # Nếu chưa đủ, thêm sản phẩm random
        if len(recommendations) < top_n:
            remaining = top_n - len(recommendations)
            random_products = random.sample(
                [p for p in self.all_products if str(p['product_id']) != str(product_id)],
                min(remaining, len(self.all_products) - 1)
            )
            for p in random_products:
                recommendations.append({
                    'product_id': p['product_id'],
                    'product_name': p.get('product_name', 'Unknown'),
                    'category_name': p.get('category_name', ''),
                    'brand': p.get('brand', ''),
                    'price': p.get('price', 0),
                    'image_url': p.get('image_url', ''),
                    'reason': "Sản phẩm nổi bật",
                    'confidence': 0.50
                })
        
        return recommendations[:top_n]
    
    def _get_random_products(self, top_n=5):
        """Trả về sản phẩm ngẫu nhiên"""
        if not self.all_products:
            return []
        
        random_products = random.sample(self.all_products, min(top_n, len(self.all_products)))
        return [
            {
                'product_id': p['product_id'],
                'product_name': p.get('product_name', 'Unknown'),
                'category_name': p.get('category_name', ''),
                'brand': p.get('brand', ''),
                'price': p.get('price', 0),
                'image_url': p.get('image_url', ''),
                'reason': "Sản phẩm phổ biến",
                'confidence': 0.50
            }
            for p in random_products
        ]

# Khởi tạo recommender global
recommender = ProductRecommender()