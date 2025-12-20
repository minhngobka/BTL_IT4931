"""Product catalog schema definitions"""

from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType, IntegerType


class ProductSchema:
    """Schema for product dimension table"""
    
    @staticmethod
    def get_catalog_schema() -> StructType:
        """Schema for product catalog CSV - MUST MATCH ACTUAL CSV HEADER"""
        return StructType([
            StructField("product_id", LongType(), nullable=False),
            StructField("product_name", StringType(), nullable=True),
            StructField("brand", StringType(), nullable=True),
            StructField("category_id", LongType(), nullable=True),
            StructField("category_name", StringType(), nullable=True),
            StructField("category_code", StringType(), nullable=True),
            StructField("subcategory", StringType(), nullable=True),
            StructField("original_price", DoubleType(), nullable=True),
            StructField("discount_percent", IntegerType(), nullable=True),
            StructField("final_price", DoubleType(), nullable=True),
            StructField("rating", DoubleType(), nullable=True),
            StructField("num_reviews", IntegerType(), nullable=True),
            StructField("in_stock", BooleanType(), nullable=True),
        ])
    
    @staticmethod
    def get_hierarchy_schema() -> StructType:
        """Schema for category hierarchy"""
        return StructType([
            StructField("category_id", LongType(), nullable=False),
            StructField("category_code", StringType(), nullable=True),
            StructField("category_name", StringType(), nullable=True),
            StructField("parent_category", StringType(), nullable=True),
        ])
