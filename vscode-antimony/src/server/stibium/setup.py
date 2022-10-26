from setuptools import setup, find_packages

setup(
    name='stibium',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # If any package contains *.lark files, include them:
        "": ["*.lark"],
    }
)
