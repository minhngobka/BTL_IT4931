"""User dimension schema definitions"""

from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, 
    IntegerType, DateType
)


class UserSchema:
    """Schema for user dimension table"""
    
    @staticmethod
    def get_user_dimension_schema() -> StructType:
        """Schema for user dimension CSV"""
        return StructType([
            StructField("user_id", LongType(), nullable=False),
            StructField("user_segment", StringType(), nullable=True),
            StructField("registration_date", DateType(), nullable=True),
            StructField("country", StringType(), nullable=True),
            StructField("age_group", StringType(), nullable=True),
            StructField("loyalty_tier", StringType(), nullable=True),
        ])
