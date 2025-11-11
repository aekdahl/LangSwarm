"""
Setup configuration for langswarm-v1-compat package
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='langswarm-v1-compat',
    version='1.0.0',
    author='LangSwarm Team',
    author_email='support@langswarm.ai',
    description='Compatibility patches for LangSwarm V1 with modern dependencies',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/LangSwarm',
    project_urls={
        'Bug Tracker': 'https://github.com/yourusername/LangSwarm/issues',
        'Documentation': 'https://langswarm.readthedocs.io',
        'Source Code': 'https://github.com/yourusername/LangSwarm',
    },
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.8',
    install_requires=[
        # No hard dependencies - works with any LangChain version
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    keywords='langswarm langchain compatibility patches encoding utf-8',
    license='MIT',
    zip_safe=False,
    include_package_data=True,
)

