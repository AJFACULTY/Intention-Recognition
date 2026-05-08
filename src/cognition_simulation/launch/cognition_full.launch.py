from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # --- Arguments ---
    world_arg = DeclareLaunchArgument(
        'world', default_value='warehouse')
    model_arg = DeclareLaunchArgument(
        'model', default_value='standard',
        choices=['standard', 'lite'])
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        choices=['true', 'false'])

    # --- Simulation (TB4 + Gazebo) ---
    sim_launch_path = os.path.join(
        get_package_share_directory('cognition_simulation'),
        'launch', 'simulation.launch.py')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sim_launch_path),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'model': LaunchConfiguration('model'),
            'rviz': LaunchConfiguration('rviz'),
            'nav2': 'true',
            'slam': 'true',
        }.items()
    )

    # --- Camera Topic Bridge ---
    # Remap TB4 camera to /camera/image_raw for our perception nodes
    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='cognition_camera_bridge',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=[
            '/oakd/rgb/preview/image_raw@sensor_msgs/msg/Image[gz.msgs.Image'
        ],
        remappings=[
            ('/oakd/rgb/preview/image_raw', '/camera/image_raw')
        ]
    )

    # --- Perception Nodes ---
    # Delayed 10s to let Gazebo fully start
    gesture_node = TimerAction(
        period=10.0,
        actions=[Node(
            package='cognition_perception',
            executable='gesture_node',
            name='gesture_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )]
    )

    detection_node = TimerAction(
        period=10.0,
        actions=[Node(
            package='cognition_perception',
            executable='person_detection_node',
            name='person_detection_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )]
    )

    # --- Brain Node ---
    # Delayed 12s to let perception nodes start first
    brain_node = TimerAction(
        period=12.0,
        actions=[Node(
            package='cognition_brain',
            executable='brain_node',
            name='brain_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )]
    )

    ld = LaunchDescription([
        world_arg,
        model_arg,
        rviz_arg,
        simulation,
        camera_bridge,
        gesture_node,
        detection_node,
        brain_node,
    ])

    return ld
