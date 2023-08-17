import csv
import argparse
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

parser = argparse.ArgumentParser(
        prog='python3 calib.py',
        description='Calibrates NTC temperature from RC circuit characteristic time tau. Creates calibration file.',
        epilog='Created by Max Herrmann (CU Boulder)')

parser.add_argument('--show-plot', required=False, help='If flag included, will show the fit and data with pyplot')
parser.add_argument('-o', '--output-file', required=True, help='Name of calibration file created')
args = parser.parse_args()
output_file = args.output_file

# Enter paths to .csv files
csv_files = ['data/5d/5D_-0.1_C.csv', 'data/5d/5D_-20_C.csv', 'data/5d/5D_-30_C.csv']

# Enter temperatures corresponding to .csv file order (C)
temps = np.array([-0.1, -20, -30])

gpio24 = []
 
def sh(x, a, b, c):
    return 1/(a+b*np.log(x-73)+c*(np.log(x-73))**3)

for file in csv_files:
    # Expects a data file of form collected by max_OHMmeter.py etc., will average "GPIO24" to one value for fit
    gpio24_f = []
    with open(file, 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]
        for line in lines[1:]:
            gpio24_f.append(float(line[2]))
    gpio24.append(gpio24_f)

gpio24 = np.array([np.average(p) for p in gpio24])

# Gets in the ballpark for some reason
p0 = np.array([-2.008881003e-3, 9.926762276e-4, -39.58085841e-7])

popt, pcov = curve_fit(sh, gpio24, temps+273, p0=p0)

# Prints fit parameters for SH NTC function
print(popt)

# If you want to see the fit plotted against the data
if args.show_plot:
    plt.scatter(gpio24, temps)
    plt.plot(np.linspace(1,8000), [sh(gp, *popt)-273 for gp in np.linspace(1,8000)])
    plt.show()

with open(output_file, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(popt)
