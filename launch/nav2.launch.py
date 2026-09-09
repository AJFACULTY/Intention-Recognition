#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    params   = os.path.expanduser('~/cognition_ws/src/cognition_simulation/config/nav2_params.yaml')
    map_yaml = os.path.expanduser('~/maps/sim_room.yaml')
    sim_time = {'use_sim_time': True}

    map_server = Node(
        package='nav2_map_server', executable='map_server',
        name='map_server', output='screen',
        parameters=[{'yaml_filename': map_yaml, 'use_sim_time': True}])

    amcl = Node(
        package='nav2_amcl', executable='amcl',
        name='amcl', output='screen',
        parameters=[params, sim_time])

    planner = Node(
        package='nav2_planner', executable='planner_server',
        name='planner_server', output='screen',
        parameters=[params, sim_time])

    controller = Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=[params, sim_time])

    behaviors = Node(
        package='nav2_behaviors', executable='behavior_server',
        name='recoveries_server', output='screen',
        parameters=[params, sim_time])

    bt_navigator = Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[params, sim_time])

    waypoint = Node(
        package='nav2_waypoint_follower', executable='waypoint_follower',
        name='waypoint_follower', output='screen',
        parameters=[params, sim_time])

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'bond_timeout': 4.0,
            'node_names': [
                'map_server',
                'amcl',
                'planner_server',
                'controller_server',
                'recoveries_server',
                'bt_navigator',
                'waypoint_follower',
            ],
        }])

    return LaunchDescription([
        map_server, amcl, planner, controller,
        behaviors, bt_navigator, waypoint, lifecycle_manager,
    ])
