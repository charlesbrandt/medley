from setuptools import setup
#from distutils.core import setup

setup(
    name='Medley',
    version='0.1.0',
    author='Charles Brandt',
    author_email='code@charlesbrandt.com',
    packages=['medley'],
    scripts=[],
    url='https://github.com/charlesbrandt/medley/',
    license='LICENSE.txt',
    description='Objects to help process and sort collections and their contents.',
    long_description=open('README.md').read(),
    install_requires=[
    ],
)
