from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='hardlinker',
      version=version,
      description="Find identical files and hardlink them",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='John Villalovos, Ralph Bean',
      author_email='ralph.bean@gmail.com',
      url='http://github.com/ralphbean/hardlinker',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
