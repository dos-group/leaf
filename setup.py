import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

if __name__ == "__main__":
    setup(
        name='leafsim',
        use_scm_version=True,
        author="Philipp Wiesner",
        author_email="wiesner@tu-berlin.de",
        description="Simulator for modeling energy consumption in cloud, fog, and edge computing environments",
        long_description=long_description,
        long_description_content_type='text/markdown',
        keywords=["simulation", "modeling", "fog computing", "energy consumption", "edge computing"],
        url="https://github.com/dos-group/leaf",
        project_urls={
            "Bug Tracker": "https://github.com/dos-group/leaf/issues",
            "Documentation": "https://leaf.readthedocs.io/",
        },
        packages=["leaf"],
        license="MIT",
        python_requires=">=3.6",
        setup_requires=['setuptools_scm'],
        install_requires=[
            'networkx~=2.5',
            'numpy~=1.19',
            'pandas~=1.1',
            'simpy~=4.0',
            'tqdm~=4.0',
        ],
        extras_require={
            "docs": ["sphinx", "alabaster"]
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Topic :: Education",
            "Topic :: Scientific/Engineering",
            "Topic :: Scientific/Engineering :: Information Analysis",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Distributed Computing",
            "Typing :: Typed",
        ],
    )
