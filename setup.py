from setuptools import setup

setup(
    name="LangSwarm",
    version="0.0.16",
    author="Alexander Ekdahl",
    description="A multi-agent ecosystem for large language models (LLMs) and autonomous systems.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aekdahl/langswarm",
    packages=["langswarm"],
    install_requires=[
        "LangSwarm-Cortex>=0.0.16",  # Core package
        #"LangSwarm-Cortex>=1.0.0",  # Memory management and self-reflection
        #"LangSwarm-Synapse>=1.0.0",  # Consensus, aggregation, voting, branching
        #"LangSwarm-Profiler>=1.0.0",  # Profiling LLMs, agents, and prompts
        #"LangSwarm-Memory>=1.0.0",  # Centralized and cross-agent memory
        #"LangSwarm-RL>=1.0.0",  # RL-based workflow orchestration
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
