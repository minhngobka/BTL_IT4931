# Cấu trúc:
```
spark_streaming/
│
├── src/                 
│   ├── __init__.py
│   ├── main.py           # Entry point: khởi tạo Spark, đọc Kafka, xử lý
│   ├── consumer.py       # Hàm đọc dữ liệu từ Kafka
│   ├── processor.py      # Xử lý dữ liệu (map, filter, aggregation)
│   └── writer.py         # Ghi dữ liệu ra console / DB / Kafka khác
│
├── config/               # Config Spark / Kafka (tùy chọn)
│   └── spark_conf.yaml
├── scripts/              # Script submit Spark job (tùy chọn)
│   └── submit.sh
└── logs/                 # Log Spark Streaming
```