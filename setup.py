"""
Big Data Customer Journey Analytics
====================================
Real-time e-commerce customer journey analytics using Apache Spark, Kafka, and MongoDB.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bigdata-customer-journey",
    version="1.0.0",
    author="BTL_IT4931",
    description="Real-time customer journey analytics with Spark Streaming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/minhngobka/BTL_IT4931",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "customer-journey-stream=app.jobs.streaming.advanced_streaming:main",
            "customer-journey-ml=app.jobs.batch.ml_analytics:main",
            "event-simulator=app.utils.event_simulator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["config/*.env"],
    },
)
