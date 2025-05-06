#!/bin/bash

# Set project root path
project_root="/home/ARO.local/yakirh/Projects/yakirs_thesis/thesis"

# Ensure the directory exists before proceeding
if [ -d "$project_root" ]; then
    cd "$project_root" || { echo "Failed to change directory to $project_root"; exit 1; }
    git pull origin main 2>&1
    echo "Project updated from the main branch."
else
    echo "Error: project root directory does not exist: $project_root"
    exit 1
fi
