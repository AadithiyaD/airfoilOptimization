# Script to clean up workspace after an optimization run
rm ./data/output/*.txt
rm ./data/airfoils/*.dat
rm *.bl
rm xfoilCommands*.txt

sed -i '1!d' ./data/optimization_datalog.csv