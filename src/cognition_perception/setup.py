from setuptools import find_packages, setup

package_name = 'cognition_perception'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models',
            ['cognition_perception/models/hand_landmarker.task']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='j',
    maintainer_email='j@todo.todo',
    description='Perception layer for the cognition robot system',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gesture_node = cognition_perception.gesture_node:main',
            'person_detection_node = cognition_perception.person_detection_node:main',
        ],
    },
)