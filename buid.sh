#!/bin/bash

set -e # Stop on error

# Clean previous builds
rm -rf build lambda_function.zip

# Create build directory
mkdir -p build

# Install dependencies to build/
pip install -r requirements.txt -t build/

# Copy your Lambda function code
cp lambda_function.py build/

# Package everything from inside build/
cd build
zip -r ../lambda_function.zip .
cd ..
