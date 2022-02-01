import json
import sys
import csv
import os
import re
import collections
import ast
from urllib.request import urlopen

def dir_maker(region):
	path = "DATA_RIPE/" + region + "_pairs/"

	try: 
	    os.mkdir(path) 
	except OSError as error: 
	    # print(error) 
	    pass

def process_command_line():
	'''returns the command argument'''
	n = len(sys.argv)
	args = []
	for i in range(1, n):
		args.append(sys.argv[i])
	return args

#this function returns a region name
def init():
	command = process_command_line()

	region = command[0]
	dir_maker(region)

	return region


def load_ASN(region):
	path = "DATA_RIPE/" + region + '/'
	with open(path + region + "_ASN.json" , 'r') as in_file:
		data_json = json.load(in_file)

	ASN_ary = (data_json['data']['countries'][0]['routed'])
	
	ret = re.findall('\((.*?)\)', ASN_ary)

	return ret

def get_query_time(region):
	path = "DATA_RIPE/" + region + '/'
	with open(path + region + "_ASN.json" , 'r') as in_file:
		data_json = json.load(in_file)

	return data_json['messages'][0][1]


def load_path(region, key):
	path = "DATA_RIPE/" + region + '/'
	data_json = {}
	try:
		with open(path + key + "_paths.json" , 'r') as infile:
				data_json = json.load(infile)
			# print(path_ary)
	except EnvironmentError:
		# print(key + " not found")
		pass


	return data_json

def get_pair_path(region):

	AS_ary = load_ASN(region)

	print('here')
	for asn in AS_ary:
		data = load_path(region, asn)
		for path in data:
			for i in range(len(path)):
				if path[i] in AS_ary:
					if path[i] == asn:
						continue
					if path[-1] != asn:
						continue
					path_dir = "DATA_RIPE/" + region + "_pairs/AS" + path[i] + "_AS" + asn + ".json"
					file1 = open(path_dir, "a+")
					file1.write(str(path[i:]))
					file1.write('\n')
					file1.close()
					# print('1')


def reduce_duplicate_path(region):
	path_dir = "DATA_RIPE/" + region + "_pairs/"
	for filename in os.listdir(path_dir):
		temp = open(path_dir + filename, 'r')
		# print(filename)
		data = temp.read().splitlines()
		new_data = []
		for i in data:
			ap = ast.literal_eval(i)
			if ap not in new_data:
				new_data.append(ap)

		temp.close()

		with open(path_dir + filename, 'w') as outfile:
			json.dump(new_data, outfile)

		final = []
		with open(path_dir + filename, 'r') as infile:
			data = json.load(infile)
			for path in data:
				result = list(dict.fromkeys(path))
				# print(result)
				if result not in final:
					final.append(result)

		with open(path_dir + filename, 'w') as outfile:
			json.dump(final, outfile)

	return


def stat_report(region, asn):
	path_dir = "DATA_RIPE/" + region + "_pairs/"
	link = "https://stat.ripe.net/data/rir-stats-country/data.json?resource="
	AS_ary = load_ASN(region)
	ret = []
	count = 0
	l = len(asn)
	for filename in os.listdir(path_dir):
		if filename[:l + 2] == 'AS' + asn:
			flag = 0
			pair = {}
			pair["all"] = []
			pair['out'] = []
			with open(path_dir + filename, 'r') as infile:
				data = json.load(infile)
				for path in data:
					mark = 0
					buf = []
					for i in path:
						if i not in AS_ary:
							response = urlopen(link + i)
							data_json = json.loads(response.read())
							loc = data_json["data"]["located_resources"][0]["location"]
							flag = 1
							mark = 1
						else:
							loc = region
						buf.append((i, loc))
					if mark == 1:
						pair['out'].append(buf)
						count += 1
					pair['all'].append(buf)
			if flag == 1:
				ret.append(pair)



	return count, ret


if __name__ == '__main__':
	region = init()

	print(get_query_time(region))

	AS_ary = load_ASN(region)


	get_pair_path(region)

	reduce_duplicate_path(region)

	count = 0
	uni = 0
	d = collections.defaultdict(int)
	for i in AS_ary:
		c, res = (stat_report(region, i))
		if c == 0:
			continue
			print("*---------------------------------------------------------------------------*")

		print("AS start: " + i,  "out: " + str(len(res)))
		for x in res:
			print(i, "->", x['all'][0][-1][0])
			print("External connection / Total connection:")
			print( len(x['out']), '/', len(x['all']))
			if len(x['out']) == len(x['all']):
				uni += 1
			
			count += 1
			for j in x:
				print(j + ": ")
				for k in x[j]:
					print(k)
					for y in k:
						if y[1] != region:
							d[y[1]] += 1
		print()

	print(uni, '/', count)

	for i in d:
		print(i,':', int(d[i]/2))


