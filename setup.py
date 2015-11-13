from distutils.core import setup

setup(
    name='tworld',
    packages=['tworld'],
    version='0.1.0',
    description='Unofficial T world API for Python.',
    long_description=open('README.rst').read(),
    license='MIT License',
    author='Suyeol Jeon',
    author_email='devxoul@gmail.com',
    url='https://github.com/devxoul/tworld',
    keywords=['tworld'],
    classifiers=[],
    install_requires=[
        'requests',
    ]
)
