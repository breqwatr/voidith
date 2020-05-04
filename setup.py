"""Set up Voidith """
from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="voidith",
    packages=find_packages(),
    version="1.00",
    license="",
    description="Breqwatr's private cloud helper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kyle Pericak",
    author_email="kyle@breqwatr.com",
    download_url="https://github.com/breqwatr/voidith/archive/1.00.tar.gz",
    url="https://github.com/breqwatr/voidith",
    keywords=["Breqwatr", "Openstack", "Kolla", "Ceph", "Docker"],
    install_requires=["flake8", "pylint", "black", "pytest"],
    entry_points="""
        [console_scripts]
        voidith=voidith.cli.main:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
    ],
)
