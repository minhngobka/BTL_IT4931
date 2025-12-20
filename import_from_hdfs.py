#!/usr/bin/env python3
"""
Import dimension tables from HDFS to MongoDB
Reads CSV files from HDFS and inserts into MongoDB collections
"""

import os
import sys
from dotenv import load_dotenv
from pyspark.sql import SparkSession
import pandas as pd
from db.mongo_client import db

# Load environment
load_dotenv()
HDFS_NAMENODE = os.getenv('HDFS_NAMENODE', 'hdfs://localhost:9000')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# HDFS paths
HDFS_CATALOG_PATH = f'{HDFS_NAMENODE}/data/catalog'
HDFS_RAW_PATH = f'{HDFS_NAMENODE}/data/raw'

def create_spark_session():
    """Create Spark session with HDFS support"""
    try:
        spark = SparkSession.builder \
            .appName("ImportFromHDFS") \
            .master("local[*]") \
            .config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE) \
            .config("spark.driver.memory", "2g") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        print(f"✅ Spark session created")
        print(f"   - HDFS: {HDFS_NAMENODE}")
        return spark
    except Exception as e:
        print(f"❌ Failed to create Spark session: {e}")
        sys.exit(1)

def read_from_hdfs(spark, hdfs_path, file_name):
    """Read CSV from HDFS"""
    full_path = f'{hdfs_path}/{file_name}'
    try:
        print(f"\n📖 Reading from HDFS: {full_path}")
        # Read all columns as strings to avoid datetime issues
        df_spark = spark.read.csv(full_path, header=True, inferSchema=False)
        
        # Convert to Pandas
        df_pandas = df_spark.toPandas()
        print(f"   ✅ Read {len(df_pandas)} rows")
        return df_pandas
    except Exception as e:
        print(f"   ❌ Error reading {full_path}: {e}")
        return None

def import_user_dimension(spark):
    """Import user dimension table to MongoDB"""
    print("\n" + "="*60)
    print("📊 IMPORTING USER DIMENSION TABLE")
    print("="*60)
    
    df = read_from_hdfs(spark, HDFS_CATALOG_PATH, 'user_dimension.csv')
    if df is None:
        return False
    
    try:
        # Drop existing collection
        if 'user_dimension' in db.list_collection_names():
            db.user_dimension.drop()
            print("   🗑️  Dropped existing user_dimension collection")
        
        # Insert to MongoDB
        records = df.to_dict('records')
        result = db.user_dimension.insert_many(records)
        print(f"   ✅ Inserted {len(result.inserted_ids)} user records")
        
        # Create indexes
        db.user_dimension.create_index([("user_id", 1)])
        db.user_dimension.create_index([("segment", 1)])
        print("   📑 Created indexes on user_id, segment")
        
        # Verify
        count = db.user_dimension.count_documents({})
        sample = db.user_dimension.find_one()
        print(f"   ✅ Verified: {count} users in MongoDB")
        print(f"   📋 Sample user: {sample.get('user_id')} - {sample.get('segment')}")
        return True
    except Exception as e:
        print(f"   ❌ Error importing user_dimension: {e}")
        return False

def import_product_catalog(spark):
    """Import product catalog to MongoDB"""
    print("\n" + "="*60)
    print("📦 IMPORTING PRODUCT CATALOG")
    print("="*60)
    
    df = read_from_hdfs(spark, HDFS_CATALOG_PATH, 'product_catalog.csv')
    if df is None:
        return False
    
    try:
        # Drop existing collection
        if 'product_catalog' in db.list_collection_names():
            db.product_catalog.drop()
            print("   🗑️  Dropped existing product_catalog collection")
        
        # Insert to MongoDB
        records = df.to_dict('records')
        result = db.product_catalog.insert_many(records)
        print(f"   ✅ Inserted {len(result.inserted_ids)} products")
        
        # Create indexes
        db.product_catalog.create_index([("product_id", 1)])
        db.product_catalog.create_index([("category", 1)])
        db.product_catalog.create_index([("brand", 1)])
        print("   📑 Created indexes on product_id, category, brand")
        
        # Verify
        count = db.product_catalog.count_documents({})
        sample = db.product_catalog.find_one()
        print(f"   ✅ Verified: {count} products in MongoDB")
        print(f"   📋 Sample product: {sample.get('product_id')} - {sample.get('product_name')}")
        return True
    except Exception as e:
        print(f"   ❌ Error importing product_catalog: {e}")
        return False

def import_category_hierarchy(spark):
    """Import category hierarchy to MongoDB"""
    print("\n" + "="*60)
    print("🏷️  IMPORTING CATEGORY HIERARCHY")
    print("="*60)
    
    df = read_from_hdfs(spark, HDFS_CATALOG_PATH, 'category_hierarchy.csv')
    if df is None:
        return False
    
    try:
        # Drop existing collection
        if 'category_hierarchy' in db.list_collection_names():
            db.category_hierarchy.drop()
            print("   🗑️  Dropped existing category_hierarchy collection")
        
        # Insert to MongoDB
        records = df.to_dict('records')
        result = db.category_hierarchy.insert_many(records)
        print(f"   ✅ Inserted {len(result.inserted_ids)} categories")
        
        # Create indexes
        db.category_hierarchy.create_index([("category_id", 1)])
        db.category_hierarchy.create_index([("category_name", 1)])
        db.category_hierarchy.create_index([("parent_id", 1)])
        print("   📑 Created indexes on category_id, category_name, parent_id")
        
        # Verify
        count = db.category_hierarchy.count_documents({})
        sample = db.category_hierarchy.find_one()
        print(f"   ✅ Verified: {count} categories in MongoDB")
        print(f"   📋 Sample category: {sample.get('category_name')}")
        return True
    except Exception as e:
        print(f"   ❌ Error importing category_hierarchy: {e}")
        return False

def main():
    """Main import flow"""
    print("\n" + "="*60)
    print("🚀 HDFS TO MONGODB IMPORT STARTED")
    print("="*60)
    print(f"   HDFS Namenode: {HDFS_NAMENODE}")
    print(f"   MongoDB: {MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Import all dimension tables
        success_user = import_user_dimension(spark)
        success_product = import_product_catalog(spark)
        success_category = import_category_hierarchy(spark)
        
        # Summary
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"   User Dimension:    {'✅ SUCCESS' if success_user else '❌ FAILED'}")
        print(f"   Product Catalog:   {'✅ SUCCESS' if success_product else '❌ FAILED'}")
        print(f"   Category Hierarchy:{'✅ SUCCESS' if success_category else '❌ FAILED'}")
        
        # Show collection sizes
        print("\n📈 MongoDB Collections:")
        for collection_name in ['user_dimension', 'product_catalog', 'category_hierarchy']:
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name}: {count} documents")
        
        if success_user and success_product and success_category:
            print("\n✅ ALL IMPORTS COMPLETED SUCCESSFULLY!")
            return 0
        else:
            print("\n⚠️  Some imports failed. Check logs above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Import failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        spark.stop()
        print("\n✅ Spark session stopped")

if __name__ == "__main__":
    sys.exit(main())
