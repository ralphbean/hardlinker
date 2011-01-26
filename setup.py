from setuptools import setup, find_packages
import sys, os

from hardlinker import __version__

setup(name='hardlinker',
      version=__version__,
      description="Find identical files and hardlink them",
      long_description="""Forked from hardlink.py by John L. Villalovos""",
      classifiers=[],
      keywords='',
      author='Ralph Bean',
      author_email='ralph.bean@gmail.com',
      url='http://github.com/ralphbean/hardlinker',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      scripts=['scripts/hardlink.py'], # blame pfmeec@rit.edu
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
