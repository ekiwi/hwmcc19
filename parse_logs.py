#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re
from typing import List
import pandas as pd

err_re = [
	('sample',          re.compile(r'sample:\s+(\d+\.\d+) time, (\d+\.\d+) real, (\d+) MB')),
	('real time limit', re.compile(r'real time limit:\s+(\d+) seconds')),
	('space limit',     re.compile(r'space limit:\s+(\d+) MB')),
	('arg0',            re.compile(r'argv\[0\]:\s+\.\/([\w\.-]+)')),
	('status',          re.compile(r'status:\s+(\w[\w ]+)')),
	('result',          re.compile(r'result:\s+(d+)')),
	('real',            re.compile(r'real:\s+(\d+.\d+) seconds')),
	('space',           re.compile(r'space:\s+(\d+) MB')),
]

def parse_err(lines: List[str], ignore_samples:bool=False) -> dict:
	dd = {'samples': []}

	for line in lines:
		if not line.startswith('[runlim]'): #skip
			continue
		line = line[len('[runlim]'):].strip()
		found_match = False
		for name, pattern in err_re:
			m = pattern.match(line)
			if m is not None:
				found_match = True
				r = m.groups()
				if name == 'sample':
					if not ignore_samples:
						dd['samples'].append({'time': float(r[0]), 'real': float(r[1]), 'mem': int(r[2])})
				elif name in {'real time limit', 'space limit', 'result', 'space'}:
					dd[name] = int(r[0])
				elif name == 'real':
					dd[name] = float(r[0])
				elif name in {'arg0', 'status'}:
					dd[name] = str(r[0])
				else:
					assert False, f"TODO: handle: {name} : {r}"
		#if not found_match: print("SKIPPING: ", line)
	return dd

def parse_log(lines: List[str]) -> dict:
	dd = {}
	for line in lines:
		if not line.startswith('c '): # skip
			continue
		parts = line[2:].strip().split(':')
		name = parts[0].strip()
		value = ':'.join(parts[1:]).strip()
		if name in {'benchmark', 'solver', 'solver options'}:
			dd[name] = value
	return dd

def parse_entry(path: str, name: str) -> dict:
	err_file = os.path.join(path, name + '.err')
	log_file = os.path.join(path, name + '.log')
	assert os.path.isfile(err_file), f"Not a file: {err_file}"
	assert os.path.isfile(log_file), f"Not a file: {log_file}"

	with open(err_file) as ff: err_content = ff.readlines()
	with open(log_file) as ff: log_content = ff.readlines()

	err_dict = parse_err(err_content, ignore_samples=True)
	log_dict = parse_log(log_content)

	benchmark_parts = log_dict['benchmark'].split('/')
	hwmcc_pos = next(ii for ii,nn in enumerate(benchmark_parts) if nn.startswith('hwmcc'))
	benchmark_with_ext = os.path.join(*benchmark_parts[hwmcc_pos+1:])
	benchmark = os.path.splitext(benchmark_with_ext)[0]

	solver = path.split('/')[-1]

	entry = {
		'status': err_dict['status'],
		'runtime': err_dict['real'],
		'max_mem': err_dict['space'],
		'benchmark': benchmark,
		'solver': solver,
		'cmd': log_dict['solver'],
		'options': log_dict['solver options'],
	}

	return entry

def find_all_entries(path: str):
	assert os.path.isdir(path), f"Not a directory: {path}"
	entries = pd.DataFrame()
	for root, _, files in os.walk(path):
		for filename in files:
			if filename.endswith('.err'):
				ee = parse_entry(root, os.path.splitext(filename)[0])
				entries = entries.append(ee, ignore_index=True)
	return entries


if __name__ == '__main__':
	# path = os.path.join('hwmcc19-single-logs', 'bv', 'cosa2')
	# ee = parse_entry(path, 'mann-unknown-ridecore')
	# print(ee)

	entries = find_all_entries('hwmcc19-single-logs')
	outfile = os.path.join('hwmcc19-single.csv')
	with open(outfile, 'w') as ff:
		entries.to_csv(ff)
	print(f"Wrote entry table to: {outfile}")