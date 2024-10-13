from distutils.core import setup


setup(
    name="homeassistant-vt100",
    version="1.1.0",
    description="VT-100 Home Assistant Frontend",
    author="DragonMinded",
    license="Public Domain",
    packages=[
        "vthass",
    ],
    install_requires=[
        req for req in open("requirements.txt").read().split("\n") if len(req) > 0
    ],
    python_requires=">3.8",
    entry_points={
        "console_scripts": [
            "homeassistant-vt100 = vthass.__main__:cli",
        ],
    },
)
