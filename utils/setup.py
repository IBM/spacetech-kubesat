from setuptools import setup, find_packages

setup(
    name="kubesat",
    version="1.0",
    url="https://github.com/IBM/spacetech-kubesat",
    packages=find_packages(
        exclude=[
            "test_utils",
            "test_utils.*"
        ]
    ),
    license="Apache License 2.0",
    keywords=[
        "space",
        "reinforcement learning"
    ],
    install_requires=[
        "aiohttp==3.6",
        "fastapi==0.58",
        "asyncio-nats-client==0.10",
        "aiologger==0.5",
        "jsonschema==3.2",
        "redis==3.5",
        "uvicorn==0.11.5",
        "numpy==1.19.0",
        "kubernetes"
    ]
)
