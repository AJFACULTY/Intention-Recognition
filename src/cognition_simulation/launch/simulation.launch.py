from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Arguments
    world_arg = DeclareLaunchArgument(
        'world', default_value='warehouse',
        description='Gazebo world: warehouse, maze, depot')

    model_arg = DeclareLaunchArgument(
        'model', default_value='standard',
        choices=['standard', 'lite'],
        description='TurtleBot4 model')

    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        choices=['true', 'false'],
        description='Launch RViz')

    nav2_arg = DeclareLaunchArgument(
        'nav2', default_value='true',
        choices=['true', 'false'],
        description='Launch Nav2')

    slam_arg = DeclareLaunchArgument(
        'slam', default_value='true',
        choices=['true', 'false'],
        description='Launch SLAM')

    x_arg = DeclareLaunchArgument('x', default_value='0.0')
    y_arg = DeclareLaunchArgument('y', default_value='0.0')
    z_arg = DeclareLaunchArgument('z', default_value='0.0')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='0.0')

    # TurtleBot4 Gazebo launch
    tb4_gz = get_package_share_directory('turtlebot4_gz_bringup')
    tb4_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb4_gz, 'launch', 'turtlebot4_gz.launch.py')),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'model': LaunchConfiguration('model'),
            'rviz': LaunchConfiguration('rviz'),
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
            'z': LaunchConfiguration('z'),
            'yaw': LaunchConfiguration('yaw'),
        }.items()
    )

    # TurtleBot4 spawn with Nav2 + SLAM
    tb4_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb4_gz, 'launch', 'turtlebot4_spawn.launch.py')),
        launch_arguments={
            'model': LaunchConfiguration('model'),
            'nav2': LaunchConfiguration('nav2'),
            'slam': LaunchConfiguration('slam'),
            'rviz': LaunchConfiguration('rviz'),
            'use_sim_time': 'true',
        }.items()
    )

    ld = LaunchDescription([
        world_arg, model_arg, rviz_arg,
        nav2_arg, slam_arg,
        x_arg, y_arg, z_arg, yaw_arg,
        tb4_launch,
    ])

    return ld
