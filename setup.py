# setup.py
from setuptools import setup, find_packages

setup(
    name="arduino-colab-kernel",
    version="0.1.0",
    description="Jupyter magics for Arduino/ESP32",
    packages=find_packages(include=["arduino_colab_kernel", "arduino_colab_kernel.*"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["pyserial", "ipython"],
)
