#!/usr/bin/env python3
"""
Publication-Quality Report Figure Generator Forwarder
Redirects to generate_reengineered_figures.py to produce the single source of truth
for all 6 publication-grade production architectural diagrams:
1. hardware_design.png: Mechatronic hardware layout & signal flow
2. system_architecture.png: End-to-end cognitive architecture & data pipeline
3. fig_spatial_zone.png: Camera FOV spatial acceptance zone & bystander rejection
4. fig_feature_pipeline.png: 4-stage geometric feature extraction pipeline (Real Hand Landmarks)
5. fig_brain_state_machine.png: UML state machine with preemption logic
6. fig_docker_deployment.png: Multi-node container deployment architecture
"""
import sys
import os

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_reengineered_figures import generate_all_production_figures

if __name__ == '__main__':
    generate_all_production_figures()
