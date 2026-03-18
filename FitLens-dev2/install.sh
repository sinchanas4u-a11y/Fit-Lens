#!/bin/bash

echo "============================================================"
echo "Body Measurement Application - Installation Script"
echo "============================================================"
echo ""

echo "Step 1: Installing PyTorch with CUDA 11.8..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
if [ $? -ne 0 ]; then
    echo "ERROR: PyTorch installation failed"
    exit 1
fi
echo ""

echo "Step 2: Installing Detectron2..."
pip install 'git+https://github.com/facebookresearch/detectron2.git'
if [ $? -ne 0 ]; then
    echo "ERROR: Detectron2 installation failed"
    exit 1
fi
echo ""

echo "Step 3: Installing other dependencies..."
pip install -r requirements_rcnn.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Dependencies installation failed"
    exit 1
fi
echo ""

echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "Running installation test..."
python test_installation.py
echo ""
echo "============================================================"
echo "Ready to use!"
echo "Run: python main.py"
echo "============================================================"
