"""
Setup configuration for Karere package.

This file is used to provide package metadata for pip installations
and to ensure importlib.metadata can access version information.
"""

from setuptools import setup, find_packages
import os


def get_version():
    """Get version from meson.build file."""
    meson_build_path = os.path.join(os.path.dirname(__file__), 'meson.build')
    if os.path.exists(meson_build_path):
        with open(meson_build_path, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'version:' in line and 'project(' in content:
                    version_part = line.split('version:')[1].strip()
                    version_str = version_part.split(',')[0].strip().strip("'\"")
                    if version_str:
                        return version_str
    return "0.1.9"


def get_long_description():
    """Get long description from README.md."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


setup(
    name='karere',
    version=get_version(),
    author='Thiago Fernandes',
    author_email='140509353+tobagin@users.noreply.github.com',
    description='A modern GTK4 WhatsApp client for Linux',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/tobagin/karere',
    project_urls={
        'Bug Reports': 'https://github.com/tobagin/karere/issues',
        'Source': 'https://github.com/tobagin/karere',
        'Discussions': 'https://github.com/tobagin/karere/discussions',
    },
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
    install_requires=[
        'PyGObject>=3.42.0',
    ],
    extras_require={
        'dev': [
            'importlib-metadata>=4.0.0; python_version<"3.8"',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Environment :: X11 Applications :: GTK',
        'Topic :: Communications :: Chat',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
    ],
    keywords='whatsapp, gtk4, libadwaita, webkit, messaging, chat',
    entry_points={
        'console_scripts': [
            'karere=karere.main:main',
        ],
    },
)