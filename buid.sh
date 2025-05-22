#!/bin/bash

set -e # Stop on error

# Clean previous builds
rm -rf detection guardduty_formatter.zip
rm -rf respone ec2_isolation_handler.zip

# Create detection directory
mkdir -p detection

# Install dependencies to detection/
pip install -r requirements.txt -t detection/

# Copy Lambda function code
cp guardduty_formatter.py detection/

# Package everything from inside detection/
cd detection
zip -r ../guardduty_formatter.zip .
cd ..

# Create respone directory
mkdir -p response

# Install dependencies to respone/
pip install -r requirements.txt -t response/

# Copy lambda function code
cp ec2_isolation_handler.py response

# Package everything from inside response/
cd response
zip -r ../ec2_isolation_handler.zip .
cd ..
