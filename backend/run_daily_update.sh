#!/bin/bash

# Daily Update Runner Script for CyberRAG
# Runs at 3 AM via cron

# paths
PROJECT_DIR="/Users/manishabasnet/Desktop/Codes/CyberRAG/backend"
CONDA_ENV_PYTHON="/Users/manishabasnet/miniconda3/envs/cyberrag/bin/python3"
LOG_FILE="$PROJECT_DIR/update.log"
ERROR_LOG="$PROJECT_DIR/update_error.log"

# Adds timestamp to log
echo "======================================" >> "$LOG_FILE"
echo "Update started at: $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

# Navigates to backend directory
cd "$PROJECT_DIR" || exit 1

# Activate conda environment and run update
"$CONDA_ENV_PYTHON" daily_update.py >> "$LOG_FILE" 2>> "$ERROR_LOG"

# Check exit status
if [ $? -eq 0 ]; then
    echo "✓ Update completed successfully at: $(date)" >> "$LOG_FILE"
else
    echo "✗ Update failed at: $(date)" >> "$ERROR_LOG"
fi

echo "" >> "$LOG_FILE"