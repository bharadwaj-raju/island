import sys

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def normalize_land_water(data, threshold=0.1):
	
	res = [[0 for i in range(len(data))] for j in range(len(data))]
	for idv, vline in enumerate(data):
		for idh, hcell in enumerate(vline):
			if hcell >= threshold:
				res[idv][idh] = 1
	return res


def normalize_0_1(data):
	
	res = [[0 for i in range(len(data))] for j in range(len(data))]
	for idv, vline in enumerate(data):
		maxval = max(vline)
		minval = min(vline)
		for idh, hcell in enumerate(vline):
			try:
				res[idv][idh] = (hcell - minval)/(maxval - minval)
			except ZeroDivisionError:
				res[idv][idh] = (hcell - minval)
	return res


def read_data_from_hmap_file(fname):
	data = []
	with open(fname) as f:
		for line in f:
			data.append([float(x) for x in line.split()])
	return data


def main():
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')

	data = read_data_from_hmap_file(sys.argv[1])

	x = list(range(len(data)))
	y = list(range(len(data)))

	X, Y = np.meshgrid(x, y)
	Z = np.array(data)
	
	ax.plot_surface(X, Y, Z, cmap='terrain')
	ax.set_zlim([0, 1.5])
	
	plt.show()

if __name__ == '__main__':
	main()