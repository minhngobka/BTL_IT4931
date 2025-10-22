# BTL_IT4931
IT4931_2025-1
                 ┌────────────────────────────┐
                 │   Data Sources (Producers) │
                 │ ─ Clickstream, Purchase    │
                 │ ─ User Behavior (Kafka)    │
                 └────────────┬───────────────┘
                              │
                              ▼
             ┌────────────────────────────────────┐
             │         Message Queue Layer         │
             │         (Apache Kafka)              │
             └──────────────────┬──────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
     ┌──────────────────────┐       ┌──────────────────────────┐
     │ Batch Layer (Spark)  │       │ Speed Layer (Spark Str.) │
     │ ─ Process HDFS data  │       │ ─ Process Kafka streams  │
     │ ─ Aggregations, ML   │       │ ─ Real-time metrics      │
     └──────────┬───────────┘       └──────────┬───────────────┘
                │                              │
                ▼                              ▼
     ┌──────────────────────┐       ┌──────────────────────┐
     │  Serving Layer       │ <──── │  NoSQL DB (Cassandra │
     │  (Unified View)      │       │  or MongoDB)         │
     └──────────┬───────────┘       └──────────┬───────────┘
                │                              │
                ▼                              ▼
        ┌──────────────────────────┐
        │ Visualization Layer       │
        │ (Grafana / Superset /     │
        │  Streamlit / Power BI)    │
        └──────────────────────────┘
