from setuptools import find_packages, setup

package_name = 'cognition_brain'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='j',
    maintainer_email='j@todo.todo',
    description='Brain/decision layer for the cognition robot system',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'brain_node = cognition_brain.brain_node:main',
        ],
    },
)
