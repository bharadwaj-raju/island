SimplexIslandGen:
	mkdir -p bin
	c++ Generators/Simplex/IslandGen.cpp -lm -o bin/SimplexIslandGen

clean:
	rm -rf bin

all:
	SimplexIslandGen

.PHONY: SimplexIslandGen all clean