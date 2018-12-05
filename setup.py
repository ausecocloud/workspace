import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'HISTORY.rst')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_oidc',
    'pyramid_cors',
    'pyramid_openapi',
    'python-keystoneclient',
    'python-swiftclient',
    'PyYAML',
    'waitress',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',
    'pytest-cov',
]

setup(
    name='workspace',
    version='0.0',
    description='Multi user workspace manager',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Environment :: Web Environment",
        'Framework :: Pyramid',
        "License :: OSI Approved :: Apache Software License"
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid',
    license='Apache License 2.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = workspace:main',
        ],
    },
)
