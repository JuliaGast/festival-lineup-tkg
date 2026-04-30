#!/bin/bash
#SBATCH --partition=gpu-vram-48gb 
#SBATCH --mem=500G
#SBATCH --cpus-per-task=10
#SBATCH --time=120:00:00
#SBATCH --output=x_cogn_%j.log
#SBATCH --error=x_cogn_%j.log
#SBATCH --gres=gpu:1
export HOME="/home/jgasting"



# Initialize Conda properly
source $HOME/miniconda3/etc/profile.d/conda.sh
# # Activate Conda environment
conda activate statictgb
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"

echo "HOME: $HOME"
echo "Using Python from: $(which python3)"
echo "Conda Environment: $(conda info --envs | grep '*' | awk '{print $1}')"



start=$(date +%s)
echo "Start time: $(date)"


python -u  main.py 

end=$(date +%s)
echo "End time : $(date)"
runtime=$((end - start))
echo "Runtime: ${runtime} seconds"



