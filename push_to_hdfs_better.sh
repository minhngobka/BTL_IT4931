#!/bin/bash
# Push local CSV files to HDFS

echo "🚀 Pushing CSV files to HDFS..."

# Kiểm tra files tồn tại
if [ ! -f "data/catalog/user_dimension.csv" ]; then
    echo "❌ user_dimension.csv not found locally. Run dimension_generator.py first."
    exit 1
fi

echo "📤 Files to upload:"
ls -lh data/catalog/*.csv

# Tạo thư mục trên HDFS nếu chưa có
echo -e "\n📁 Creating HDFS directories..."
docker exec namenode hdfs dfs -mkdir -p /data/catalog
docker exec namenode hdfs dfs -mkdir -p /data/raw

# Copy files vào container trước
CONTAINER_ID=$(docker ps -q -f name=namenode)
echo -e "\n📦 Copying files to namenode container..."

docker cp data/catalog/user_dimension.csv $CONTAINER_ID:/tmp/user_dimension.csv && \
    echo "   ✅ user_dimension.csv copied" || echo "   ❌ user_dimension.csv failed"

docker cp data/catalog/product_catalog.csv $CONTAINER_ID:/tmp/product_catalog.csv && \
    echo "   ✅ product_catalog.csv copied" || echo "   ❌ product_catalog.csv failed"

docker cp data/catalog/category_hierarchy.csv $CONTAINER_ID:/tmp/category_hierarchy.csv && \
    echo "   ✅ category_hierarchy.csv copied" || echo "   ❌ category_hierarchy.csv failed"

# Upload từ container lên HDFS
echo -e "\n📤 Uploading to HDFS..."

docker exec namenode hdfs dfs -put -f /tmp/user_dimension.csv /data/catalog/user_dimension.csv && \
    echo "   ✅ user_dimension.csv uploaded" || echo "   ❌ user_dimension.csv failed"

docker exec namenode hdfs dfs -put -f /tmp/product_catalog.csv /data/catalog/product_catalog.csv && \
    echo "   ✅ product_catalog.csv uploaded" || echo "   ❌ product_catalog.csv failed"

docker exec namenode hdfs dfs -put -f /tmp/category_hierarchy.csv /data/catalog/category_hierarchy.csv && \
    echo "   ✅ category_hierarchy.csv uploaded" || echo "   ❌ category_hierarchy.csv failed"

# Verify
echo -e "\n✅ Verification:"
docker exec namenode hdfs dfs -ls -h /data/catalog/

echo -e "\n🎉 Done!"
