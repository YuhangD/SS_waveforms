#/bin/zsh

for info_f in `ls ./Info/Bin1_*xlsx`
do
    python rate_data.py ${info_f} --prefix './' --suffix '.BHT.sac' --plot-command 'python plot_wiggle.py {file}' 
done
