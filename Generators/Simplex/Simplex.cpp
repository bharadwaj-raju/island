#include <array>
#include <vector>
#include <random>
#include <algorithm>
#include <math.h>

int grad3[12][3] = {
	{1,1,0}, {-1,1,0}, {1,-1,0}, {-1,-1,0},
	{1,0,1}, {-1,0,1}, {1,0,-1}, {-1,0,-1},
	{0,1,1}, {0,-1,1}, {0,1,-1}, {0,-1,-1}
};

namespace Simplex {

std::vector<int> get_permutation_table(unsigned seed) {

	std::array<int,256> perm1;

	for (int i = 0; i < 256; i++) {
		perm1[i] = i;
	}

	// shuffle permutation table
	std::shuffle(perm1.begin(), perm1.end(), std::default_random_engine(seed));

	// the permutation table is repeated twice
	std::array<int,256> perm2(perm1);

	std::vector<int> perm;

	perm.insert(perm.end(), perm1.begin(), perm1.end());
	perm.insert(perm.end(), perm2.begin(), perm2.end());

	perm[512] = perm1[256];

	return perm;

}

float calculate_gradient(int x, int y, int size) {
	
	float distance_x = fabs(x - size * 0.5);
	float distance_y = fabs(y - size * 0.5);
	float distance = sqrt(distance_x*distance_x + distance_y*distance_y);
	float max_width = size * 0.5 - 10.0;
	float delta = distance / max_width;
	
	return delta * delta;

}

float dot2d(int * subgrad, float x, float y) {
	return ((subgrad[0]*x) + (subgrad[1]*y));
}

int fastfloor(float n) {
	if (n < 0) {
		return (int)(n - 1);
	}
	else {
		return (int)(n);
	}
}

float raw_noise_2d(std::vector<int> perm, float x, float y) {

	// Skew the input space to determine which simplex cell were in
	float F2 = 0.5 * (sqrt(3.0) - 1.0);
	
	// Hairy skew factor for 2D
	float s = (x + y) * F2;
	int i = fastfloor(x + s);
	int j = fastfloor(y + s);

	float G2 = (3.0 - sqrt(3.0)) / 6.0;
	float t = (float)(i + j) * G2;
	
	// Unskew the cell origin back to (x,y) space
	float X0 = i - t;
	float Y0 = j - t;
	
	// The x,y distances from the cell origin
	float x0 = x - X0;
	float y0 = y - Y0;

	// For the 2D case, the simplex shape is an equilateral triangle.
	// Determine which simplex we are in.
	int i1, j1 = 0; // Offsets for second (middle) corner of simplex in (i,j) coords
	if (x0 > y0) { // lower triangle, XY order: (0,0)->(1,0)->(1,1)
		i1 = 1;
		j1 = 0;
	}
	else {		// upper triangle, YX order: (0,0)->(0,1)->(1,1)
		i1 = 0;
		j1 = 1;
	}

	// A step of (1,0) in (i,j) means a step of (1-c,-c) in (x,y), and
	// a step of (0,1) in (i,j) means a step of (-c,1-c) in (x,y), where
	// c = (3-sqrt(3))/6
	float x1 = x0 - i1 + G2;	   // Offsets for middle corner in (x,y) unskewed coords
	float y1 = y0 - j1 + G2;
	float x2 = x0 - 1.0 + 2.0 * G2;  // Offsets for last corner in (x,y) unskewed coords
	float y2 = y0 - 1.0 + 2.0 * G2;

	// Work out the hashed gradient indices of the three simplex corners
	int ii = i & 255;
	int jj = j & 255;
	int gi0 = perm[ii+perm[jj]] % 12;
	int gi1 = perm[ii+i1+perm[jj+j1]] % 12;
	int gi2 = perm[ii+1+perm[jj+1]] % 12;

	// Calculate the contribution from the three corners
	float t0 = 0.5 - x0*x0 - y0*y0;
	float n0 = 0.0;
	if (! (t0 < 0)) {
		t0 *= t0;
		n0 = t0 * t0 * dot2d(grad3[gi0], x0, y0);
	}

	float t1 = 0.5 - x1*x1 - y1*y1;
	float n1 = 0.0;
	if (! (t1 < 0)) {
		t1 *= t1;
		n1 = t1 * t1 * dot2d(grad3[gi1], x1, y1);
	}

	float t2 = 0.5 - x2*x2-y2*y2;
	float n2 = 0.0;
	if (! (t2 < 0)) {
		t2 *= t2;
		n2 = t2 * t2 * dot2d(grad3[gi2], x2, y2);
	}

	// Add contributions from each corner to get the final noise value.
	// The result is scaled to return values in the interval [-1,1].
	return (70.0 * (n0 + n1 + n2));

}

float octave_noise_2d(std::vector<int> perm, int octaves, float persistence, float scale, float x, float y) {

	float total = 0.0;
	float frequency = scale;
	float amplitude = 1.0;

	// We have to keep track of the largest possible amplitude,
	// because each octave adds more, and we need a value in [-1, 1].
	float maxAmplitude = 0.0;

	for (int i = 0; i < octaves; i++) {
		total += raw_noise_2d(perm, x * frequency, y * frequency) * amplitude;
		frequency *= 2.0;
		maxAmplitude += amplitude;
		amplitude *= persistence;
	}

	return (total / maxAmplitude);

}

float scaled_octave_noise_2d(std::vector<int> perm, int octaves, float persistence, float scale, float lbound, float ubound, float x, float y) {
	float octave_noise = octave_noise_2d(perm, octaves, persistence, scale, x, y);
	return (octave_noise * (ubound - lbound) / 2 + (ubound + lbound) / 2);
}

}  // namespace Simplex