
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


def generate_user_dimension(num_users=10000, csv_file_path='2019-Oct.csv'):
    """
    Generate user dimension table with demographics and segmentation
    """
    print(f"Generating user dimension for {num_users} users...")
    
    # Read actual user IDs from the event data
    try:
        df_events = pd.read_csv(csv_file_path, nrows=100000)
        actual_user_ids = df_events['user_id'].unique()[:num_users]
        print(f"Found {len(actual_user_ids)} unique users from event data")
    except:
        print("Event data not found, generating random user IDs")
        actual_user_ids = range(1, num_users + 1)
    
    # Demographics
    segments = ['High-Value', 'Regular', 'Occasional', 'New', 'At-Risk']
    segment_weights = [0.1, 0.3, 0.3, 0.2, 0.1]
    
    countries = ['USA', 'UK', 'Germany', 'France', 'Spain', 'Italy', 
                 'Canada', 'Australia', 'Japan', 'Brazil']
    country_weights = [0.25, 0.15, 0.1, 0.1, 0.08, 0.08, 0.08, 0.06, 0.05, 0.05]
    
    cities_by_country = {
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
        'UK': ['London', 'Manchester', 'Birmingham', 'Glasgow', 'Liverpool'],
        'Germany': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'],
        'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'],
        'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao'],
        'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence'],
        'Canada': ['Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Ottawa'],
        'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'],
        'Japan': ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya'],
        'Brazil': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza']
    }
    
    # Generate registration dates (last 2 years)
    end_date = datetime(2019, 10, 31)
    start_date = end_date - timedelta(days=730)
    
    users = []
    for user_id in actual_user_ids:
        country = np.random.choice(countries, p=country_weights)
        city = np.random.choice(cities_by_country[country])
        segment = np.random.choice(segments, p=segment_weights)
        
        # Registration date (weighted toward more recent)
        days_ago = int(np.random.exponential(180))
        if days_ago > 730:
            days_ago = 730
        registration_date = end_date - timedelta(days=days_ago)
        
        users.append({
            'user_id': int(user_id),
            'user_segment': segment,
            'registration_date': registration_date.strftime('%Y-%m-%d'),
            'country': country,
            'city': city,
            'age_group': np.random.choice(['18-24', '25-34', '35-44', '45-54', '55+'], 
                                         p=[0.15, 0.35, 0.25, 0.15, 0.1]),
            'gender': np.random.choice(['M', 'F', 'Other'], p=[0.48, 0.48, 0.04]),
            'preferred_language': country if country != 'USA' else 'English'
        })
    
    df_users = pd.DataFrame(users)
    output_file = 'data/catalog/user_dimension.csv'
    df_users.to_csv(output_file, index=False)
    print(f"✓ User dimension saved to {output_file}")
    print(f"  Rows: {len(df_users)}")
    print(f"  Columns: {list(df_users.columns)}")
    print(f"\nSample data:")
    print(df_users.head())
    
    return df_users


def generate_enhanced_product_catalog(csv_file_path='2019-Oct.csv'):
    """
    Generate enhanced product catalog with hierarchy and attributes
    """
    print("\nGenerating enhanced product catalog...")
    
    try:
        # Read actual product data from events
        df_events = pd.read_csv(csv_file_path, nrows=500000)
        
        # Get unique products with their basic info
        df_products = df_events[['product_id', 'category_id', 'brand', 'price']].drop_duplicates('product_id')
        
        # Parse category codes if available
        if 'category_code' in df_events.columns:
            df_events['category_code'] = df_events['category_code'].fillna('unknown')
            
            # Extract category hierarchy
            df_events['main_category'] = df_events['category_code'].apply(
                lambda x: x.split('.')[0] if isinstance(x, str) and '.' in x else 'uncategorized'
            )
            df_events['subcategory'] = df_events['category_code'].apply(
                lambda x: x.split('.')[1] if isinstance(x, str) and '.' in x and len(x.split('.')) > 1 else ''
            )
            
            # Join with products
            category_map = df_events[['product_id', 'category_code', 'main_category', 'subcategory']].drop_duplicates('product_id')
            df_products = df_products.merge(category_map, on='product_id', how='left')
        else:
            df_products['category_code'] = 'electronics.smartphone'
            df_products['main_category'] = 'electronics'
            df_products['subcategory'] = 'smartphone'
        
        # Generate product names based on category
        def generate_product_name(row):
            category = row.get('main_category', 'product')
            brand = row.get('brand', 'Generic')
            if pd.isna(brand):
                brand = 'Generic'
            return f"{brand} {category.title()} Model {random.randint(100, 999)}"
        
        df_products['product_name'] = df_products.apply(generate_product_name, axis=1)
        df_products['category_name'] = df_products['main_category'].apply(lambda x: x.title() if pd.notna(x) else 'Uncategorized')
        
        # Add additional attributes
        df_products['rating'] = np.random.uniform(3.0, 5.0, len(df_products)).round(1)
        df_products['num_reviews'] = np.random.randint(0, 1000, len(df_products))
        df_products['in_stock'] = np.random.choice([True, False], len(df_products), p=[0.85, 0.15])
        df_products['discount_percent'] = np.random.choice([0, 5, 10, 15, 20, 25], len(df_products), 
                                                           p=[0.5, 0.2, 0.15, 0.1, 0.03, 0.02])
        
        # Calculate discounted price
        df_products['original_price'] = df_products['price']
        df_products['discount_amount'] = (df_products['original_price'] * df_products['discount_percent'] / 100).round(2)
        df_products['final_price'] = (df_products['original_price'] - df_products['discount_amount']).round(2)
        
        # Clean up
        df_products = df_products.fillna({
            'brand': 'Generic',
            'category_code': 'unknown',
            'subcategory': '',
            'category_name': 'Uncategorized'
        })
        
        # Select final columns
        output_columns = [
            'product_id', 'product_name', 'brand', 'category_id', 'category_name',
            'category_code', 'subcategory', 'original_price', 'discount_percent',
            'final_price', 'rating', 'num_reviews', 'in_stock'
        ]
        
        df_products = df_products[output_columns]
        
        output_file = 'data/catalog/product_catalog.csv'
        df_products.to_csv(output_file, index=False)
        print(f"✓ Product catalog saved to {output_file}")
        print(f"  Rows: {len(df_products)}")
        print(f"  Columns: {list(df_products.columns)}")
        print(f"\nSample data:")
        print(df_products.head())
        
        return df_products
        
    except Exception as e:
        print(f"Error generating product catalog: {e}")
        print("Creating minimal product catalog...")
        
        # Fallback: create minimal catalog
        products = []
        for i in range(1000):
            products.append({
                'product_id': i + 1,
                'product_name': f"Product {i+1}",
                'category_name': np.random.choice(['Electronics', 'Clothing', 'Home', 'Sports']),
                'category_code': 'electronics.smartphone',
                'subcategory': 'smartphone'
            })
        
        df_products = pd.DataFrame(products)
        df_products.to_csv('data/catalog/product_catalog.csv', index=False)
        print(f"✓ Minimal product catalog created")
        return df_products


def generate_category_hierarchy():
    """
    Generate category hierarchy table
    """
    print("\nGenerating category hierarchy...")
    
    categories = [
        # Electronics
        {'category_id': 1, 'category_name': 'Electronics', 'parent_category': None, 
         'level': 1, 'description': 'Electronic devices and accessories'},
        {'category_id': 101, 'category_name': 'Smartphones', 'parent_category': 'Electronics',
         'level': 2, 'description': 'Mobile phones and smartphones'},
        {'category_id': 102, 'category_name': 'Laptops', 'parent_category': 'Electronics',
         'level': 2, 'description': 'Laptop computers and notebooks'},
        {'category_id': 103, 'category_name': 'Audio', 'parent_category': 'Electronics',
         'level': 2, 'description': 'Headphones, speakers, and audio equipment'},
        
        # Clothing
        {'category_id': 2, 'category_name': 'Clothing', 'parent_category': None,
         'level': 1, 'description': 'Apparel and fashion items'},
        {'category_id': 201, 'category_name': 'Men', 'parent_category': 'Clothing',
         'level': 2, 'description': 'Men\'s clothing and accessories'},
        {'category_id': 202, 'category_name': 'Women', 'parent_category': 'Clothing',
         'level': 2, 'description': 'Women\'s clothing and accessories'},
        {'category_id': 203, 'category_name': 'Kids', 'parent_category': 'Clothing',
         'level': 2, 'description': 'Children\'s clothing'},
        
        # Home
        {'category_id': 3, 'category_name': 'Home', 'parent_category': None,
         'level': 1, 'description': 'Home goods and furniture'},
        {'category_id': 301, 'category_name': 'Furniture', 'parent_category': 'Home',
         'level': 2, 'description': 'Home furniture'},
        {'category_id': 302, 'category_name': 'Kitchen', 'parent_category': 'Home',
         'level': 2, 'description': 'Kitchen appliances and tools'},
        
        # Sports
        {'category_id': 4, 'category_name': 'Sports', 'parent_category': None,
         'level': 1, 'description': 'Sports equipment and apparel'},
        {'category_id': 401, 'category_name': 'Fitness', 'parent_category': 'Sports',
         'level': 2, 'description': 'Fitness equipment and accessories'},
        {'category_id': 402, 'category_name': 'Outdoor', 'parent_category': 'Sports',
         'level': 2, 'description': 'Outdoor sports and camping gear'}
    ]
    
    df_categories = pd.DataFrame(categories)
    output_file = 'data/catalog/category_hierarchy.csv'
    df_categories.to_csv(output_file, index=False)
    print(f"✓ Category hierarchy saved to {output_file}")
    print(f"  Rows: {len(df_categories)}")
    print(f"\nSample data:")
    print(df_categories.head(10))
    
    return df_categories


def generate_all_dimensions(csv_file_path='2019-Oct.csv'):
    """
    Generate all dimension tables
    """
    print("=" * 80)
    print("Generating All Dimension Tables")
    print("=" * 80)
    print()
    
    # Generate dimensions
    df_users = generate_user_dimension(num_users=5000, csv_file_path=csv_file_path)
    df_products = generate_enhanced_product_catalog(csv_file_path=csv_file_path)
    df_categories = generate_category_hierarchy()
    
    print("\n" + "=" * 80)
    print("All Dimension Tables Generated Successfully!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  1. user_dimension.csv")
    print("  2. product_catalog.csv (enhanced)")
    print("  3. category_hierarchy.csv")
    print("\nThese files are ready to be used in the Spark applications.")


if __name__ == "__main__":
    # Check if event data exists
    import os
    
    csv_file = '2019-Oct.csv'
    if not os.path.exists(csv_file):
        print(f"Warning: {csv_file} not found!")
        print("Please download the dataset from Kaggle first.")
        print("Link: https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store")
        print("\nGenerating dimension tables with sample data anyway...")
    
    generate_all_dimensions(csv_file)
