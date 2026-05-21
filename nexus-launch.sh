#!/bin/bash

# PSN Launch Script
alias nexus-ui='streamlit run ui/nexus_dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false'

echo "PSN Environment Loaded."
echo "Use 'nexus-ui' to launch the dashboard."
