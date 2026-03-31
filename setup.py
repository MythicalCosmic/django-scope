from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-scope",
    version="1.0.0",
    author="MythicalCosmic",
    author_email="qodirjonov0854@gmail.com",
    description="A real-time debugging and monitoring dashboard for Django — monitor requests, queries, cache, Redis, exceptions, and more.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MythicalCosmic/django-scope",
    project_urls={
        "Bug Tracker": "https://github.com/MythicalCosmic/django-scope/issues",
        "Documentation": "https://github.com/MythicalCosmic/django-scope/wiki",
        "Source": "https://github.com/MythicalCosmic/django-scope",
    },
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "django>=4.2",
        "channels>=4.0",
        "daphne>=4.2.1",
    ],
    extras_require={
        "redis": ["redis>=4.0", "django-redis>=5.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Framework :: Django :: 4",
        "Framework :: Django :: 5",
        "Framework :: Django :: 6",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: System :: Monitoring",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="django debugging monitoring observability websocket scope dashboard profiling",
    python_requires=">=3.10",
)