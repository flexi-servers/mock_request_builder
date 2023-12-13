from distutils.core import setup

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(name='mock_request_builder',
      version='2.0',
      description='A generator for simple SQLAlchemy models endpoints in FastAPI',
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=setuptools.find_packages(),
      author='Maximilian Kutschka von Rothenfels',
      author_email='admin@flexi-servers.com',
      url='https://github.com/flexi-servers/mock_request_builder',
      python_requires='>=3.10',
      install_requires=[
            "sqlalchemy >=2.0.0",
            "fastapi >=0.98.0",
      ],
)