# Script to clean up workspace after an optimization run
rm ./data/temp/*.txt
rm ./data/temp/*test*.dat
rm ./data/temp/*MOO*.dat
rm ./data/final_output/*.dat
rm ./data/final_output/*.txt
rm ./postProcess_data/*.dat
rm ./postProcess_data/*.txt

rm *.bl
rm xfoil*.txt
rm *.png



cp -r postProcess_data/sampleData/. postProcess_data

sed -i '1!d' ./data/optimization_datalog.csv