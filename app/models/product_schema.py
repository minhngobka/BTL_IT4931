"""Product catalog schema definitions"""

from pyspark.sql.types import StructType, StructField, StringType, LongType


class ProductSchema:
    """Schema for product dimension table"""
    
    @staticmethod
    def get_catalog_schema() -> StructType:
        """Schema for product catalog CSV"""
        return StructType([
            StructField("product_id", LongType(), nullable=False),
            StructField("product_name", StringType(), nullable=True),
            StructField("category_name", StringType(), nullable=True),
            StructField("category_code", StringType(), nullable=True),
            StructField("subcategory", StringType(), nullable=True),
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
