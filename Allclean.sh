# Script to clean up workspace after an optimization run
rm ./data/temp/*.txt
rm ./data/temp/*.dat
rm ./data/final_output/*.dat
rm ./data/final_output/*.txt
rm *.bl
rm xfoil*.txt

sed -i '1!d' ./data/optimization_datalog.csv