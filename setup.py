from setuptools import setup, find_packages, find_namespace_packages

requirements = {"core": [], "optional": {}}
# Read dependencies from requirements.txt
with open("requirements.txt", "r") as f:
    sections = f.read().split("# Optional dependencies")  # Split the content into sections

# Process core dependencies
requirements["core"] = [line for line in sections[0].strip().splitlines() if ">=" in line.replace("==",">=")]

# Process optional dependencies
if len(sections) > 1:
    requirements["optional"] = {line.strip().replace("==",">=").split(">=")[0]:line for line in sections[1].strip().splitlines() if ">=" in line.replace("==",">=")}
    requirements["optional"]["all"] = list(set(requirements["optional"].values()))

# Add logic to install [all] by default if no extras are specified
import sys
if not any(arg.startswith("--extras") or "[" in arg for arg in sys.argv):
    requirements["core"] += requirements["optional"]["all"]
    
setup(
    name="LangSwarm",
    version="0.0.3",
    author="Alexander Ekdahl",
    description="A multi-agent ecosystem for large language models (LLMs) and autonomous systems.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aekdahl/langswarm",
    packages=find_namespace_packages(include=["langswarm.*"]),
    install_requires=requirements["core"],
    extras_require=requirements.get("optional", {}),
    author_email="alexander.ekdahl@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.8',
    include_package_data=True,
)
