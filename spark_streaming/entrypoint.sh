#!/bin/bash
set -e

if [ "$SPARK_MODE" = "master" ]; then
    echo "Starting Spark Master..."
    ${SPARK_HOME}/bin/spark-class org.apache.spark.deploy.master.Master \
        --host spark-master \
        --port 7077 \
        --webui-port 8080
elif [ "$SPARK_MODE" = "worker" ]; then
    echo "Starting Spark Worker..."
    ${SPARK_HOME}/bin/spark-class org.apache.spark.deploy.worker.Worker \
        ${SPARK_MASTER_URL} \
        --webui-port 8081
else
    exec sleep infinity
fi