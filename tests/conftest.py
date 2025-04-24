# ONLY FOR LOCAL TESTING
# SHOULD BE REMOVED

# conftest.py
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir) + '/engage-dag-dependencies'

# Add your custom paths
sys.path.insert(0, parentdir)
sys.path.insert(0, '/Users/alexanderekdahl/Development/engage-dag-dependencies')
sys.path.insert(0, '/Users/alexanderekdahl/miniforge3/lib/python3.8/site-packages')
