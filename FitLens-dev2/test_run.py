import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from processing.smplifyx_runner import run_smplifyx

run_smplifyx('data/images/front.jpg', 'data/images/side.jpg')
