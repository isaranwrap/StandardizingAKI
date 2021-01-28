from setuptools import setup

with open('README.md', 'r') as f:
      long_description = f.read() 
setup(
      name = 'akiFlagger',
      version = '0.3.2',
      description = 'Flagger to detect patients with acute kidney injury (AKI).',
      py_modules = ['akiFlagger'],
      package_dir = {'':'src'},
      classifiers = [
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent'
      ],
      long_description = long_description,
      long_description_content_type = 'text/markdown',
      install_requires=[
            "numpy",
            "pandas",
      ],
      url = 'https://github.com/isaranwrap/StandardizingAKI',
      project_urls = {
            'Documentation': 'https://akiflagger.readthedocs.io/en/latest/',
      },
)