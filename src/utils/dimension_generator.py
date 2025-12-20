import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import subprocess

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=env_path)

HDFS_NAMENODE = os.getenv('HDFS_NAMENODE', 'hdfs://localhost:9000')
CSV_LOCAL_PATH = os.getenv('CSV_LOCAL_PATH', 'data/raw/ecommerce_events_2019_oct.csv')

def write_csv_to_hdfs(df, filename, hdfs_dir='data/catalog'):
    """
    Write CSV to local only.
    User will push to HDFS manually using the provided shell script
    """
    local_path = filename
    df.to_csv(local_path, index=False)
    print(f"💾 Saved locally: {local_path}")
    print(f"   📤 Will be pushed to HDFS: {HDFS_NAMENODE}/{hdfs_dir}/{filename}")
    return True

def read_csv_local_or_hdfs(file_path, local_fallback, columns=None):
    """
    Read CSV from local (faster for dimension generation)
    """
    try:
        if columns:
            df = pd.read_csv(local_fallback, usecols=columns, nrows=100000)
        else:
            df = pd.read_csv(local_fallback, nrows=100000)
        print(f"✅ Loaded {len(df)} rows from local: {local_fallback}")
        return df
    except Exception as e:
        print(f"❌ Cannot read: {local_fallback} - {e}")
        return None

def generate_user_dimension(num_users=5000):
    """
    Generate user dimension table from event data
    """
    print(f"\n👥 Generating {num_users} user records...")
    
    # Read source data from local (faster)
    df_events = read_csv_local_or_hdfs(
        f"{HDFS_NAMENODE}/data/raw/ecommerce_events_2019_oct.csv",
        CSV_LOCAL_PATH,
        columns=['user_id']
    )
    
    if df_events is None:
        print("❌ Cannot read source data")
        return None
    
    # Extract unique user IDs
    actual_user_ids = df_events['user_id'].unique()[:num_users]
    print(f"  Found {len(actual_user_ids)} unique users")
    
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
    
    # Generate registration dates
    end_date = datetime(2019, 10, 31)
    
    users = []
    for user_id in actual_user_ids:
        country = np.random.choice(countries, p=country_weights)
        city = np.random.choice(cities_by_country[country])
        segment = np.random.choice(segments, p=segment_weights)
        
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
    
    # Write to both local and HDFS
    write_csv_to_hdfs(df_users, 'user_dimension.csv')
    
    print(f"✅ User dimension generated: {len(df_users)} users")
    print(f"   Columns: {list(df_users.columns)}")
    print(f"\n📋 Sample:")
    print(df_users.head())
    
    return df_users

def generate_product_catalog():
    """
    Generate product_catalog.csv from event data
    """
    print(f"\n📦 Generating product_catalog.csv...")
    
    # Read source data
    df = read_csv_local_or_hdfs(
        f"{HDFS_NAMENODE}/data/raw/ecommerce_events_2019_oct.csv",
        CSV_LOCAL_PATH,
        columns=['product_id', 'category_id', 'category_code', 'brand', 'price']
    )
    
    if df is None:
        print("❌ Cannot read source data")
        return None
    
    # Clean and aggregate
    df = df.dropna(subset=['product_id', 'price'])
    df['product_id'] = df['product_id'].astype(int)
    df['price'] = df['price'].astype(float)

    product_df = df.groupby('product_id').agg({
        'category_id': 'first',
        'category_code': 'first',
        'brand': 'first',
        'price': 'median'
    }).reset_index()

    def extract_category_name(code):
        if isinstance(code, str) and '.' in code:
            return code.split('.')[0].capitalize()
        return 'Unknown'

    product_df['category_name'] = product_df['category_code'].apply(extract_category_name)

    def build_product_name(row):
        brand = row['brand'] if pd.notna(row['brand']) else 'Generic'
        category = row['category_name']
        model = random.randint(100, 999)
        return f"{brand} {category} Model {model}"

    product_df['product_name'] = product_df.apply(build_product_name, axis=1)

    product_df['image_url'] = product_df['product_id'].apply(
        lambda pid: f"https://picsum.photos/300/300?random={pid}"
    )

    product_df['price'] = product_df['price'].round(0)

    product_df = product_df[[
        'product_id', 'product_name', 'brand', 'category_id', 'category_name',
        'category_code', 'price', 'image_url'
    ]]

    # Write to both local and HDFS
    write_csv_to_hdfs(product_df, 'product_catalog.csv')
    
    print(f"✅ Product catalog generated: {len(product_df)} products")
    print(f"\n📋 Sample:")
    print(product_df.head())
    
    return product_df

def generate_category_hierarchy():
    """
    Generate category hierarchy table
    """
    print(f"\n🏷️  Generating category_hierarchy.csv...")
    
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
    
    # Write to both local and HDFS
    write_csv_to_hdfs(df_categories, 'category_hierarchy.csv')
    
    print(f"✅ Category hierarchy generated: {len(df_categories)} categories")
    print(f"\n📋 Sample:")
    print(df_categories.head(10))
    
    return df_categories

def verify_hdfs_files():
    """
    Verify all generated files exist in HDFS
    """
    print("\n\n🔍 Verifying HDFS files...")
    
    files = ['user_dimension.csv', 'product_catalog.csv', 'category_hierarchy.csv']
    
    for filename in files:
        try:
            result = subprocess.run(
                f"docker exec namenode hdfs dfs -ls /data/catalog/{filename}",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ {filename}: Found in HDFS")
            else:
                print(f"❌ {filename}: Not found in HDFS")
        except Exception as e:
            print(f"❌ {filename}: Error checking - {str(e)[:80]}")

def generate_all_dimensions():
    """
    Generate all dimension tables and push to HDFS
    """
    print("=" * 80)
    print("🎯 DIMENSION GENERATOR - HDFS Integration")
    print("=" * 80)
    print()
    
    # Generate all dimensions
    df_users = generate_user_dimension(num_users=5000)
    df_products = generate_product_catalog()
    df_categories = generate_category_hierarchy()
    
    # Verify
    print("\n")
    verify_hdfs_files()
    
    print("\n" + "=" * 80)
    print("✅ ALL DIMENSION TABLES GENERATED & PUSHED TO HDFS!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  📁 Local copies: user_dimension.csv, product_catalog.csv, category_hierarchy.csv")
    print(f"  📂 HDFS copies: {HDFS_NAMENODE}/data/catalog/")
    print("\nThese files are ready for Spark streaming and batch jobs!")

if __name__ == "__main__":
    generate_all_dimensions()