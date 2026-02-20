rm -r thread_temp_*
rm *.db
# rm -r output/
rm -r thread_data/

clear

echo "Running script"

python3 main.py memories_history.json 20