"""Set up Voithos """
from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="voithos",
    packages=find_packages(),
    version="1.0",
    license="",
    description="Breqwatr's private cloud helper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kyle Pericak",
    author_email="kyle@breqwatr.com",
    download_url="https://github.com/breqwatr/voithos/archive/1.00.tar.gz",
    url="https://github.com/breqwatr/voithos",
    keywords=["Breqwatr", "Openstack", "Kolla", "Ceph", "Docker"],
    install_requires=["boto3", "flake8", "pylint", "black", "pytest"],
    entry_points="""
        [console_scripts]
        voithos=voithos.cli.main:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
    ],
)
