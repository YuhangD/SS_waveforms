#/bin/zsh
bin_name=$1
python rate_data.py "../Info/${bin_name}_info.xlsx" --prefix "../Data/" --suffix ".BHT.sac" --plot-command "python plot_wiggle.py {file}" --output "../Rating/${bin_name}_ratings.xlsx"

