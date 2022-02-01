
import json
import sys
import csv
import os
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import concurrent.futures
import collections
import ssl
import re
from copy import copy

#use file as input for name of the data, and the url needed

ssl._create_default_https_context = ssl._create_unverified_context


looking_glass = "https://stat.ripe.net/data/looking-glass/data.json?resource="

def dir_maker(region):
	path = "DATA_RIPE/" + region

	try:
		os.mkdir("DATA_RIPE")
	except OSError as error:
		pass

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

	if len(command) == 1:
		get_region_ASN_update(region)
		as_ary = load_ASN(region)
		prefix_ary = thread_pull_prefixes(region, as_ary)

		path_ary = thread_pull_path(prefix_ary)
		save_path(region, path_ary)
	elif command[1] == '-local':
		print("loc")
		pass


	try: 
	    os.mkdir('report/' + region) 
	except OSError as error: 
	    # print(error) 
	    pass

	return region

def get_routable_AS (region):
	link = "https://stat.ripe.net/data/country-asns/data.json?resource=" + region + "&lod=1"
	return link

def get_region_ASN_update(region):

	path = "DATA_RIPE/" + region

	try: 
	    os.mkdir(path) 
	except OSError as error: 
	    # print(error) 
	    pass

	response = urlopen(get_routable_AS(region))
	data_json = json.loads(response.read())
	path = "DATA_RIPE/" + region + "/"

	with open(path + region + "_ASN.json" , 'w+') as outfile:
		json.dump(data_json, outfile)

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



def get_AS_prefixes(ASN):
	ASN_routing_hist_url = "https://stat.ripe.net/data/routing-history/data.json?resource=AS" + ASN

	prefix_ary = []

	max_try = 2
	attempt = 0
	while (attempt < max_try):
		try:
			response = urlopen(ASN_routing_hist_url, timeout = 60)
			data_json = json.loads(response.read())
			for i in data_json['data']['by_origin'][0]['prefixes']:
				# print(i)
				temp = i['prefix']

				prefix_ary.append(temp)
			break
		except:
		    print("attempt No.", str(attempt))
		    attempt += 1
		    continue

	return prefix_ary


def thread_pull_prefixes(region, AS_ary):
	with concurrent.futures.ThreadPoolExecutor() as executor:
		future = [executor.submit(get_AS_prefixes, AS) for AS in AS_ary]
		prefix_ary = [f.result() for f in future]
	data_json = {}
	data_json['date'] = get_query_time(region)
	data_json['prefixes'] = []
	for i in prefix_ary:
		data_json['prefixes'] += i

	path = "DATA_RIPE/" + region + '/'

	with open(path + region + "_prefixes.json" , 'w+') as outfile:
		json.dump(data_json, outfile)
	# print(path_ary)


	return data_json['prefixes']



def load_region_prefixes(region):
	path = "DATA_RIPE/" + region + '/'
	with open(path + region + "_prefixes.json" , 'r') as infile:
			data_json = json.load(infile)
		# print(path_ary)


	return data_json['prefixes']



def get_path(ip):
	path_ary = {}
	path_ary[ip] = []
	max_try = 2
	attempt = 0
	while (attempt < max_try):
		try:
			response = urlopen(looking_glass + ip, timeout = 60)
			data_json = json.loads(response.read())
			if(data_json['data']['rrcs'] != []):
				for j in data_json['data']['rrcs']:
					for k in j['peers']:
						# print(k['as_path'])
						# print(type(k['as_path']))
						x = (k['as_path']).split(" ")
						path_ary[ip].append(x)
			break
		except:
		    print("attempt No.", str(attempt))
		    attempt += 1
		    continue


	return path_ary


def thread_pull_path(ips):
	with concurrent.futures.ThreadPoolExecutor() as executor:
		future = [executor.submit(get_path, ip) for ip in ips]
		path_ary = [f.result() for f in future]

	# print(path_ary)
	ret = {}
	for i in path_ary:
		for key in i:
			if i[key] == []:
				continue
			else:
				ret[key] = i[key]


	return ret

def save_path(region, paths):
	path = "DATA_RIPE/" + region + '/'
	res = collections.defaultdict(list)
	for key in paths:
		if paths[key] != []:
			res[paths[key][0][-1]] += paths[key]

	for key in res:
		with open(path + key + "_paths.json" , 'w+') as outfile:
			json.dump(res[key], outfile)


	return


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



def make_within_mat(region, ASN_ary):
	length = len(ASN_ary)
	temp = set()

	ret_dict = []
	ret = []
	buf = collections.defaultdict(int)
	for i in range(length):
		temp.add(ASN_ary[i])
		buf[ASN_ary[i]] = -1


	for i in range(length):
		ret_dict.append(copy(buf))
		ret_dict[i][ASN_ary[i]] = 1
		path_buf = load_path(region, ASN_ary[i])
		if path_buf == {}:
			# print('nothing')
			continue
		# print('here')

		for j in path_buf:
			for k in range(len(j)):
				if j[k] in ret_dict[i]:
					for x in j[k:]:
						if x not in ret_dict[i]:
							if ret_dict[i][j[k]] == 1:
								break
							else:
								ret_dict[i][j[k]] = 0
								break
								
					if x == j[-1]:
						ret_dict[i][j[k]] = 1


	for i in range(len(ret_dict)):
		ret.append([])
		for k, v in ret_dict[i].items():
			ret[i].append(v)

	mat_t = [[] for i in ret]

	for i in ret:
		for j in range(len(i)):
			mat_t[j].append(i[j])



	return mat_t, ret




#make another csv file eliminate all rows which only has 1 connection
#make another heatmap


def csv_mat_maker(region, mat, ASN_ary):
	path = 'report/' + region + '/' + region + '_path_finder.csv'
	path_clean = 'report/' + region + '/' + region + '_path_finder_clean.csv'

	new_mat = []
	mat_t = [[] for i in mat]

	for i in mat:
		for j in range(len(i)):
			mat_t[j].append(i[j])



	new_AS_ary = []
	buf = []
	

	for i in range(len(mat)):
		count_row = mat[i].count(1) + mat[i].count(0)
		count_col = mat_t[i].count(1) + mat_t[i].count(0)
		if count_row <= 1 and count_col <= 1:
			buf.append(i)
		else:
			new_AS_ary.append(ASN_ary[i])

	for i in range(len(mat)):
		temp = []
		if i in buf:
			continue
		
		for j in range(len(mat[i])):
			if j not in buf:
				temp.append(mat[i][j])
		new_mat.append(temp)

	ASN_ary.insert(0, region + "_ASN")
	with open(path , 'w+', ) as myfile:
	    wr = csv.writer(myfile)
	    wr.writerow(ASN_ary)
	    for i in range(len(mat)):
	    	mat[i].insert(0, int(ASN_ary[i + 1]))
	    	wr.writerow(mat[i])

	print('Total ASN:', len(ASN_ary) - 1, '\tInactive ASN:', len(ASN_ary) - len(new_AS_ary) - 1)
	print('Inactive ASN:')
	for i in ASN_ary[1:]:
		if i not in new_AS_ary:
			print(i, end = ', ')

	print()

	new_AS_ary.insert(0, region + "_ASN")
	with open(path_clean, 'w+') as myfile:
	    wr = csv.writer(myfile)
	    wr.writerow(new_AS_ary)
	    for i in range(len(new_mat)):
	    	new_mat[i].insert(0, int(new_AS_ary[i + 1]))
	    	wr.writerow(new_mat[i])

	return new_AS_ary[1:]


def heat_map_maker (region, data_file, outname):
	df = pd.read_csv(data_file)
	df.drop(df.columns[[0]], axis = 1, inplace = True)
	
	# df.pivot('AS index', 'AS index', 'Connectivity')
	'''space out the axis labels'''
	ticks = df.index
	keptticks = ticks[::int(len(ticks)/10)]
	ticks = ['' for y in ticks]
	ticks[::int(len(ticks)/10)] = keptticks


	f, ax = plt.subplots(figsize = (14, 10))
	# ax = sns.color_palette("Spectral", as_cmap=True)
	ax = sns.heatmap(df, xticklabels = ticks, yticklabels = ticks, cmap="magma")


	plt.title(region + ' Inner AS Connectivity through Looking Glass', fontsize = 30)
	plt.ylabel('AS index', fontsize = 30)
	plt.xlabel('AS index', fontsize = 30)
	plt.savefig('report/' + region + '/' + region + '_' + outname + '.png')



def connection_stat (region, data_file):

	ret = collections.defaultdict(list)

	with open(data_file, 'r') as in_file:
		reader = csv.reader(in_file)
		temp = list(reader)
		# print(list(reader)[0])

	for l in temp[1:]:
		a = 0
		if l == []:
			continue
		for i in l[1:]:
			if int(i) > -1:
				a += 1
		
		ret[a].append(l[0])

	return ret



def outbound_stat (region, data_file):

	print('outbound connection')
	ret = collections.defaultdict(list)

	with open(data_file, 'r') as in_file:
		reader = csv.reader(in_file)
		temp = list(reader)
		# print(list(reader)[0])

	for l in temp[1:]:
		buf = 0
		k = 1
		if l == []:
			continue
		for i in l[1:]:

			if int(i) == 0:
				print(l[0], '->', temp[0][k])
				buf += 1
			k += 1
		ret[buf].append(l[0])

	return ret

def query_connection (ASN, region, data):
	ret = collections.defaultdict(list)
	ret['Out'] = []
	ret['In'] = []
	with open(data, 'r') as in_file:
		reader = csv.reader(in_file)
		temp = list(reader)
		# print(list(reader)[0])

	for l in temp[1:]:
		if l[0] == ASN:

			for i in range(len(l)):
				if i == 0:
					continue
				if l[i] == '0':
					ret['Out'].append(temp[0][i])
				elif l[i] == '1':
					ret['In'].append(temp[0][i])

	print(ASN + ": ")
	print('In:', ret['In'])
	print('Out:', ret['Out'])

	return ret

# def main():

if __name__ == '__main__':
	region = init()

	print(get_query_time(region))

	AS_ary = load_ASN(region)

	mat, mat_t = make_within_mat(region, AS_ary)
	# for i in mat:
	# 	print(i)

	# print(mat)
	# print(mat_t)

	csv_mat_maker(region, mat, AS_ary)
	heat_map_maker(region, 'report/' + region + '/' + region + '_path_finder.csv', "looking_glass")
	heat_map_maker(region, 'report/' + region + '/' + region + '_path_finder_clean.csv', "looking_glass_clean")
	res = connection_stat(region, 'report/' + region + '/' + region + '_path_finder_clean.csv')
	

	print("Inner connection stat")

	temp = []
	for k in res:
		temp.append(k)

	temp.sort()
	for i in temp:
		print('length:', len(res[i]), '\n', 'Number of connection:', i , ":", res[i])

	res_out = outbound_stat(region, 'report/' + region + '/' + region + '_path_finder_clean.csv')
	print("outbound connection stat")
	temp = []
	for k in res_out:
		temp.append(k)

	temp.sort()
	for i in temp:
		print('length:', len(res_out[i]), '\n' ,'Number of connection:', i, ":", res_out[i])

