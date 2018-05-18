import png
import io
from PIL import Image
import argparse
import json
import os
import sys

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


def normalize_0_255(norm_0_1_data):
	res = [[0 for i in range(len(norm_0_1_data))] for j in range(len(norm_0_1_data))]
	for idv, vline in enumerate(norm_0_1_data):
		for idh, hcell in enumerate(vline):
			res[idv][idh] = hcell * 255
	return res


def generate_simple_pixel_matrix(data, color_config):

	WATER_COLOR, LAND_COLOR = color_config['water'], color_config['land']

	pixels = [[0 for i in range(len(data))] for i in range(len(data))]

	WATER_VALUE = 0

	for idv, vline in enumerate(data):
		for idh, hcell in enumerate(vline):
			pixels[idv][idh] = WATER_COLOR if (hcell == WATER_VALUE) else LAND_COLOR

	return pixels


def generate_color_heights_pixel_matrix(data, color_config, threshold=0.1):

	pixels = [[0 for i in range(len(data))] for i in range(len(data))]

	HEIGHT_COLORS = color_config['color-heights']

	for idv, vline in enumerate(data):
		for idh, hcell in enumerate(vline):
			if hcell <= threshold:
				pixels[idv][idh] = HEIGHT_COLORS['0.0']

			else:
				try:
					pixels[idv][idh] = HEIGHT_COLORS[str(round(hcell, 1))]

				except KeyError:
					pixels[idv][idh] = HEIGHT_COLORS['1.0']

	return pixels


def generate_biome_pixel_matrix(elevation_data, moisture_data, color_config, threshold=0.1):

	def biome(elevation, moisture):

		if elevation <= threshold:
			return 'water'

		if elevation <= (threshold + 0.01):
			return 'beach'

		if elevation >= 0.7:
			if moisture <= 0.3:
				return 'cold-desert'
			return 'snow'

		if moisture <= 0.15:
			return 'desert'

		if moisture >= 0.9:
			return 'marshland'

		#if elevation < 0.4:
		if moisture >= 0.7:
			return 'rainforest'

		if elevation > 0.4:
			if moisture >= 0.3:
				return 'forest'

		return 'grassland'

	pixels = [[0 for i in range(len(elevation_data))] for i in range(len(elevation_data))]

	COLORS = color_config['biome']

	for idv in range(len(elevation_data)):
		for idh in range(len(elevation_data[idv])):
			elevation = elevation_data[idv][idh]
			moisture = moisture_data[idv][idh]
			pixels[idv][idh] = COLORS[biome(elevation, moisture)]

	return pixels



def make_png_file(pixels, fname, grayscale=False):

	if grayscale:
		pngimg = png.from_array(pixels, 'L')

	else:
		pngimg = png.from_array(pixels, 'RGB')

	with open(fname, 'wb') as f:
		pngimg.save(f)


def make_svg_file(pixels, fname, grayscale=False):

	if grayscale:
		pngimg = png.from_array(pixels, 'L')

	else:
		pngimg = png.from_array(pixels, 'RGB')

	pngfile = io.BytesIO()
	pngimg.save(pngfile)
	image = Image.open(pngfile).convert('RGB')
	imagedata = image.load()

	svgdata = ''
	svgdata += ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
	svgdata += ('<svg id="svg2" xmlns="http://www.w3.org/2000/svg" version="1.1" width="%(x)i" height="%(y)i" viewBox="0 0 %(x)i %(y)i">\n' % {'x':image.size[0], 'y':image.size[1]})

	for y in range(image.size[1]):
		for x in range(image.size[0]):
			rgb = imagedata[x, y]
			rgb = '#%02x%02x%02x' % rgb
			svgdata += ('<rect width="1" height="1" x="%i" y="%i" fill="%s" />\n' % (x, y, rgb))

	svgdata += ('</svg>\n')

	with open(fname, 'w') as f:
		f.write(svgdata)


def read_data_from_hmap_file(fname):
	data = []
	with open(fname) as f:
		for line in f:
			data.append([float(x) for x in line.split()])
	return data

def main():

	arg_parser = argparse.ArgumentParser(description='IslandRender — Render islands (.hmap) as images')

	arg_parser.add_argument(
		'heightmap_file', metavar='heightmap-file', type=str,
		help='The height map (.hmap) file')

	arg_parser.add_argument(
		'output_file', metavar='image-file', type=str,
		help='The output image file')

	arg_parser.add_argument(
		'--output-format', type=str,
		help='The output image format (png or svg). Default: png',
		choices=['png', 'svg'], default='png',
		required=False, metavar='png|svg')

	arg_parser.add_argument(
		'--mode', type=str,
		help='The type of image generated: either with varying colors for heights, or simple land/water, or a raw grayscale heightmap',
		choices=['color-heights', 'simple', 'heightmap', 'biome'], default='simple',
		required=False, metavar='color-heights|simple|heightmap')

	arg_parser.add_argument(
		'--water-level', type=float, default=0.2,
		help='The water or flooding level (all values below this will be rendered as water)',
		required=False)

	arg_parser.add_argument(
		'--biome-file', type=str,
		help='Optional .biome file (of same size as .hmap) to use for biome rendering mode',
		required=False)

	args = arg_parser.parse_args()

	print(args)

	data = read_data_from_hmap_file(args.heightmap_file)

	color_config = ''
	with open('IslandRenderColors.json') as f:
		for line in f:
			if not (line.strip().startswith('/*') or line.strip().startswith('//')):
				color_config += line
	color_config = json.loads(color_config)


	if args.mode == 'color-heights':
		pixels = generate_color_heights_pixel_matrix(data, color_config, threshold=args.water_level)

	elif args.mode == 'simple':
		pixels = generate_simple_pixel_matrix(normalize_land_water(data, threshold=args.water_level), color_config)

	elif args.mode == 'biome':
		if not args.biome_file:
			print('If mode is biome, then biome file must be specified with --biome-file.')
			sys.exit(1)
		moisture_data = read_data_from_hmap_file(args.biome_file)
		pixels = generate_biome_pixel_matrix(data, moisture_data, color_config, threshold=args.water_level)

	else:
		pixels = normalize_0_255(normalize_0_1(data))

	if args.mode == 'heightmap':
		grayscale = True

	else:
		grayscale = False

	if args.output_format == 'png':
		make_png_file(pixels, args.output_file, grayscale=grayscale)

	else:
		make_svg_file(pixels, args.output_file, grayscale=grayscale)


if __name__ == '__main__':
	main()
