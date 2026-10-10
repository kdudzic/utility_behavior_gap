#!/bin/bash
#SBATCH --job-name=insert-job-name-here
#SBATCH --time=00:05:00
#SBATCH --account=insert-acc-name-here
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --gres=gpu

module load CUDA
srun main.py