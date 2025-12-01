FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      procps \
      default-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV SPARK_VERSION=3.5.0
ENV SPARK_HOME=/opt/spark
ENV HADOOP_HOME=/opt/hadoop
ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"
ENV PYTHONPATH="${SPARK_HOME}/python:${PYTHONPATH}"

RUN curl -L https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz | \
    tar xz -C /opt && \
    mv /opt/spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]