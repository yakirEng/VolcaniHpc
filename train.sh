#!/bin/bash

#SBATCH --job-name=multinode_fpn
#SBATCH --partition=qgpu
#SBATCH --nodes=1  # Request 1 node (adjust as necessary)
#SBATCH --ntasks-per-node=2  # 2 tasks (GPUs) per node
#SBATCH --gres=gpu:a100:2  # Request 2 GPUs per node
#SBATCH --cpus-per-task=8
#SBATCH --mem=256G
#SBATCH --output=logs/%j.out  # SLURM output file with job ID

# Define paths
conda_path="/home/ARO.local/yakirh/anaconda3"
env_name="sat_env"
project_root="/home/ARO.local/yakirh/Projects/yakirs_thesis/thesis"
file_name="src/train.py"  # Path relative to the project root

# Activate Conda environment
source "$conda_path/etc/profile.d/conda.sh"
conda activate "$env_name"
echo "Activated Conda Environment: $env_name" 

# Set PYTHONPATH to the project root so that the 'src' module is found
export PYTHONPATH="$project_root:$PYTHONPATH"


# Debugging info
echo "Active Conda Environment: $(conda info --envs | grep '*' | awk '{print $1}')" 
echo "Using Python at: $(which python)" 
echo "Python version: $(python --version)" 
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())')" 
echo "GPU Name: $(python -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")')"

# Run the Python training script
srun python3 -u "${file_name}" 2>&1 

echo "Job completed!"


