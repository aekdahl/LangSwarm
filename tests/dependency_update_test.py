import subprocess
import requests
import sys
from packaging.version import Version


def fetch_versions(package_name):
    """
    Fetch all available versions of a package from PyPI.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        all_versions = list(response.json()["releases"].keys())
        # Sort versions using `packaging.version.Version`
        all_versions.sort(key=Version)
        return all_versions
    except requests.RequestException as e:
        print(f"Error fetching versions for {package_name}: {e}")
        return []


def test_dependency_version(package, version):
    """
    Test if a specific version of a package can be installed.
    """
    try:
        print(f"Testing {package}=={version}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"{package}=={version}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"{package}=={version} installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print(f"{package}=={version} failed.")
        return False

def find_oldest_compatible_version(package, versions):
    """
    Find the oldest compatible version of a package, biased towards the second half of the list.
    """
    if not versions:
        return None

    left = 0
    right = len(versions) - 1
    compatible_version = None

    # Start the binary search with a bias toward the second half
    while right - left > 2:
        mid = left + (right - left) // 3 * 2  # Biased towards the second half
        if test_dependency_version(package, versions[mid]):
            compatible_version = versions[mid]
            right = mid - 1  # Narrow down to the left half
        else:
            left = mid + 1  # Narrow down to the right half

    # Traverse the remaining range to confirm the oldest compatible version
    for i in range(left, right + 1):
        if test_dependency_version(package, versions[i]):
            compatible_version = versions[i]
            break

    return compatible_version

def get_supported_python_versions():
    """
    Extract the list of supported Python versions from the requirements.txt file.
    """
    supported_versions = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                if line.startswith("# Supported versions of Python:"):
                    supported_versions = line.strip().split(":")[1].strip().split(", ")
                    break
    except FileNotFoundError:
        pass
    return supported_versions


def update_requirements_with_python_versions(dependency_versions, python_version, success):
    """
    Update the requirements.txt file with the latest compatible versions
    and maintain only supported Python versions.
    """
    # Get existing supported versions
    supported_versions = set(get_supported_python_versions())
    
    if success:
        supported_versions.add(python_version)  # Add the Python version if it succeeded
    else:
        supported_versions.discard(python_version)  # Remove the version if it failed

    # Sort for consistency
    supported_versions = sorted(supported_versions)

    with open("requirements.txt", "w") as f:
        # Add the comment about supported Python versions
        f.write(f"# Supported versions of Python: {', '.join(supported_versions)}\n")
        f.write("# Automatically updated by dependency_update_test.py")

        # Write the compatible dependency versions
        f.write("\n\n# Core dependencies\n")
        for package, compatible_version in dependency_versions["core"].items():
            f.write(f"{package}>={compatible_version}\n")

        f.write("\n\n# Optional dependencies\n")
        for package, compatible_version in dependency_versions["optional"].items():
            f.write(f"{package}>={compatible_version}\n")
    print("requirements.txt updated successfully with Python version support comment.")

def assign_versions(dependencies, success):
    latest_versions = {}
    for package in dependencies:
        print(f"\nFetching versions for {package}...")
        versions = fetch_versions(package)
        if not versions:
            print(f"No versions found for {package}. Skipping...")
            continue

        print(f"Available versions for {package}: {versions}")
        compatible_version = find_oldest_compatible_version(package, versions)
        if compatible_version:
            print(f"Oldest compatible version for {package}: {compatible_version}")
            latest_versions[package] = compatible_version
        else:
            print(f"No compatible version found for {package} on Python {python_version}.")
            success = False
            break  # Exit the loop and mark the test as failed

    return latest_versions, success
    
def main(python_version):
    dependencies = {"core": [], "optional": []}
    # Read dependencies from requirements.txt
    try:
        with open("requirements.txt", "r") as f:
            sections = f.read().split("# Optional dependencies")  # Split the content into sections

        # Process core dependencies
        dependencies["core"] = [line.strip().replace("==",">=").split(">=")[0] for line in sections[0].strip().splitlines() if ">=" in line.replace("==",">=")]
        
        # Process optional dependencies
        if len(sections) > 1:
            dependencies["optional"] = [line.strip().replace("==",">=").split(">=")[0] for line in sections[1].strip().splitlines() if ">=" in line.replace("==",">=")]
        
    except FileNotFoundError:
        print("requirements.txt not found.")
        sys.exit(1)

    success = True  # Track whether all tests passed
    core, success = assign_versions(dependencies["core"], success)
    optional, success = assign_versions(dependencies["optional"], success)
    latest_versions = {"core": core, "optional": optional}

    # Update requirements.txt with compatible versions and supported Python versions
    update_requirements_with_python_versions(latest_versions, python_version, success)

    if not success:
        sys.exit(1)  # Exit with failure if any dependency test failed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dependency_update_test.py <python_version>")
        sys.exit(1)
    main(sys.argv[1])
