#!/bin/bash

# Activate the Conda environment
source /home/ARO.local/yakirh/anaconda3/etc/profile.d/conda.sh
conda activate sat_env

# Check if the MLflow server is already running
if pgrep -f "mlflow server" > /dev/null; then
    echo "MLflow server is already running."
else
    echo "Starting MLflow server..."
    mlflow server --host 0.0.0.0 --port 5000 &
    echo "MLflow server started."
fi

echo "MLflow server started on $(hostname) at port 5000."
