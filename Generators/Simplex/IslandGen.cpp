#include <iostream>
#include <string>
#include <fstream>
#include <chrono>
#include <vector>
#include <math.h>

#include "Simplex.cpp"

#define OCTAVES 16
#define PERSISTENCE 0.5f
#define SCALE_FACTOR 0.0033f  // gives good noise distribution

int main(int argc, char const *argv[]) {

	int nargs = argc - 1;

	std::string usage = "Usage: ./SimplexIslandGen SIZE OUTPUT-FILENAME [SEED or \"SEED=unset\"] [LOWER-BOUND UPPER-BOUND]";

	if (nargs < 2) {  // SIZE and OUTPUT-FILENAME not given
		std::cout << usage << std::endl;
		return 1;
	}

	int size = atoi(argv[1]);
	std::string filename = argv[2];
	unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();

	float LBOUND = 0.0f;
	float UBOUND = 1.0f;

	if (nargs >= 3) {
		if (std::string(argv[3]) != "SEED=unset") {
			seed = atoi(argv[3]);
		}
		
		if (nargs > 3 && nargs < 5) {
			std::cout << usage << std::endl;
			std::cout << "Specify both LOWER-BOUND and UPPER-BOUND" << std::endl;
			return 1;
		}
		
		else {
			if (nargs == 5) {
				LBOUND = atof(argv[4]);
				UBOUND = atof(argv[5]);
			}
		}
	}

	const float SCALING = (1024.0f / (float)size) * SCALE_FACTOR;

	std::vector<int> perm (Simplex::get_permutation_table(seed));

	std::cout << "Image size: " << size << std::endl;
	std::cout << "Saving data to filename: " << filename << std::endl;
	std::cout << "Seed (unique ID): " << seed << std::endl;
	std::cout << "Lower bound: " << LBOUND << std::endl;
	std::cout << "Upper bound: " << UBOUND << std::endl;

	std::ofstream outf;
	outf.open(filename, std::ofstream::out | std::ofstream::trunc);
	outf.close();
	outf.open(filename, std::ios::app);

	for (int x = 0; x < size; x++) {
		for (int y = 0; y < size; y++) {
			float gradient = Simplex::calculate_gradient(x, y, size);
			float val = Simplex::scaled_octave_noise_2d(perm, OCTAVES, PERSISTENCE, SCALING, LBOUND, UBOUND, (float)x, (float)y) * fmax(0.0f, 1.0f - gradient);
			outf << val << " ";
		}
		outf << std::endl;
	}

	outf.close();

	return 0;

}