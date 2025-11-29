
import pkg_resources
import sys

def check_version(package_name):
    try:
        version = pkg_resources.get_distribution(package_name).version
        print(f"{package_name}: {version}")
    except pkg_resources.DistributionNotFound:
        print(f"{package_name}: Not installed")

print(f"Python: {sys.version}")
check_version("litellm")
check_version("google-generativeai")
check_version("vertexai")
