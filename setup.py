from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='lumi',
    packages=find_packages(),
    version='1.0.11',
    description='Convert your Python functions into REST API without any extra effort 🔥',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Tanmoy Sarkar',
    author_email='ts741127@gmail.com',
    license='BSD',
    url="https://github.com/Tanmoy741127/lumi",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    keywords='rpc rest api web backend framework',
    python_requires='>=3.6',
    install_requires=[
        "nanoid==2.0.0",
        "waitress==2.1.2"
    ],

)
