echo "Washing Machine Log - $(date)" 
sudo setsid python gyrospreadx2.py >> Full_log.txt 2>&1 &