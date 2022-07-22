#!/usr/bin/env python
from __future__ import print_function

import sys
import os
import re
from make_colors import make_colors
from pydebugger.debug import debug
from datetime import datetime
from configset import configset
import psycopg2
import cmdw
import time
import argparse

try:
	from pause import pause
except ImportError:
	def pause(*args, **kwargs):
		raw_input(make_colors("enter to continue !", 'lw', 'r') + " ")

class Manage(object):

	CONFIGNAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'gogs_manage.ini')
	CONFIG = configset(CONFIGNAME)
	GOGS_USER_ID = CONFIG.get_config('gogs', 'user_id')
	GOGS_USERNAME = CONFIG.get_config('gogs', 'username')
	SOURCE_REPO = CONFIG.get_config('repo', 'source')
	ROOT_REPO = CONFIG.get_config('repo', 'root')

	def __init__(self):
		super(Manage, self)

	@classmethod
	def get_now(self):
		if sys.version_info.major == 2:
			return str(time.mktime(datetime.now().timetuple())).split(".")[0]
		else:
			return str(datetime.now().timestamp()).split(".")[0]


	@classmethod
	def format_number(self, number, length = 10):
		number = str(number).strip()
		if not str(number).isdigit():
			return number
			zeros = len(str(length)) - len(number)
			r = ("0" * zeros) + str(number)
			if len(r) == 1:
				return "0" + r
				return r

	@classmethod
	def scanning(self, path = None, destination = None):
		path = path or self.SOURCE_REPO
		if not path:
			print(make_colors("Please definition your scanning Repo Path in config or input !", 'lw', 'r'))
			sys.exit(0)
		if not os.path.isdir(path):
			print(make_colors("Invalid scanning Repo Path in config or input !", 'lw', 'r'))
			sys.exit(0)

		destination = destination or self.ROOT_REPO
		if not destination:
			print(make_colors("Please definition your root Repo Path in config or input !", 'lw', 'r'))
			sys.exit(0)
		if not os.path.isdir(destination):
			print(make_colors("Invalid root Repo Path in config or input !", 'lw', 'r'))
			sys.exit(0)

		self.SOURCE_REPO = destination

		path = set(list(filter(None, [os.path.join(path, i.split("\n")[0]) for i in os.listdir(path)])))
		debug(path = path)
		repos = []
		for i in path:
			if os.path.isdir(os.path.join(i, '.git')):
				repos.append({'name':os.path.basename(i), 'path':os.path.join(i, '.git')})
		debug(repos = repos)
		return repos

	@classmethod
	def create_link(self, target, name):
		a = os.system("ln -sf '{}' '{}'".format(target, name))
		if a == 0:
			print(
				make_colors("create link:", 'ly') + " " + \
				make_colors(target, 'lc') + " with name `" + \
				make_colors(name, 'b' 'lg')
			)
		else:
			print(
				make_colors("create link", 'ly') + " " + \
				make_colors("[ERROR]", 'lw', 'r') + ": " + \
				make_colors(target, 'lc') + " with name `" + \
				make_colors(name, 'b' 'lg')
			)

	@classmethod
	def make_db_config(self):
		db_config = "dbname={} user={} password={} port={}".format(
			self.CONFIG.get_config('db', 'name'),
			self.CONFIG.get_config('db', 'username'),
			self.CONFIG.get_config('db', 'password'),
			self.CONFIG.get_config('db', 'port', '5432'),
		)
		debug(test = re.findall("= | = ", db_config))
		if not "= " in re.findall("= | = ", db_config) and not " = " in re.findall("= | = ", db_config):
			debug(db_config = db_config)
			return db_config
		print(make_colors("Please edit database connection setting !", 'lw', 'r'))
		return False

	@classmethod
	def insert_db(self, path = None, user_id = None):
		user_id = user_id or self.GOGS_USER_ID
		if not user_id:
			user_id = self.user()
			if user_id:
				user_id = user_id[0]
		debug(user_id = user_id)
		if not user_id:
			print(make_colors("No Gogs USER_ID, please edit your config file !", 'lw', 'r'))
			sys.exit(0)
		db_config = self.make_db_config()
		if not db_config:
			sys.exit(make_colors("ERROR: config database !", 'lw', 'r'))
		repos = self.scanning(path)
		if not repos:
			print(make_colors("No Repository !", 'lw', 'r'))
			sys.exit()

		# SQL = "INSERT INTO public.repository (name, owner_id, lower_name, is_bare, is_private, is_mirror, enable_pulls, created_unix, updated_unix) VALUES ('{}', {}, '{}', '{}', '{}', '{}', '{}', {}, {})"
		# SQL1 = "UPDATE public.repository set owner_id = {}, lower_name = '{}', is_bare = 'f', is_private = 'f', is_mirror = 'f', enable_pulls = 't', created_unix = {}, updated_unix = {} WHERE name = '{}'"
		# now = self.get_now()
		for i in repos:
			debug(i = i)
			if i.get('name') and i.get('path') and self.ROOT_REPO:
				debug(i = i)
				repo_name = i.get('name')
				repo_path = i.get('path')
				
				conn = psycopg2.connect(db_config)
				cursor = conn.cursor()
				check = cursor.execute("SELECT name from public.repository WHERE name = '{}'".format(repo_name))
				conn.commit()
				data_fecth = cursor.fetchone()
				debug(data_fecth = data_fecth)
				debug(i = i)
				debug(repo_name = repo_name)
				debug(repo_path = repo_path)
				if not data_fecth:
					SQL = "INSERT INTO public.repository (name, owner_id, lower_name, is_bare, is_private, is_mirror, enable_pulls, created_unix, updated_unix) VALUES ('{}', {}, '{}', '{}', '{}', '{}', '{}', {}, {})".format(
						os.path.basename(repo_name),
						user_id,
						repo_name.lower(),
						'f',
						'f',
						'f',
						't',
						self.get_now(),
						self.get_now(),
					)
					debug(SQL = SQL)
					cursor.execute(SQL)
					conn.commit()
				else:
					debug(repo_name = repo_name)
					debug(repo_path = repo_path)
					SQL = "UPDATE public.repository set owner_id = {}, lower_name = '{}', is_bare = 'f', is_private = 'f', is_mirror = 'f', enable_pulls = 't', created_unix = {}, updated_unix = {} WHERE name = '{}'".format(user_id, repo_name.lower(), self.get_now(), self.get_now(), repo_name)
					debug(SQL = SQL)
					cursor.execute(SQL)
					conn.commit()
				print(make_colors("insert", 'lg') + " " + make_colors(repo_name, 'ly') + " " + make_colors("to database", 'lc'))
				self.create_link(repo_path, os.path.join(self.ROOT_REPO, repo_name + ".git"))
			print("-"*cmdw.getWidth())
			# pause()
	
	@classmethod
	def user(self, select = False, user_id = None):
		user_id = user_id or self.GOGS_USER_ID
		debug(user_id = user_id)
		db_config = self.make_db_config()
		debug(db_config = db_config)
		SQL = "SELECT id, name from public.user"
		debug(GOGS_USERNAME = self.GOGS_USERNAME)
		if user_id:
			SQL = "SELECT id, name from user WHERE user_id = {} FROM public.user".format(user_id)
		elif self.GOGS_USERNAME:
			SQL = "SELECT id, name from user WHERE name = {} FROM public.user".format(self.GOGS_USERNAME)
		else:
			if not user_id and not self.GOGS_USERNAME:
				print(make_colors("WARNING: No Gogs USER_ID / USERNAME, please edit your config file !", 'b', 'ly'))
			SQL = "SELECT id, name FROM public.user"

		debug(SQL = SQL)
		with psycopg2.connect(db_config) as conn:
			cursor = conn.cursor()
			cursor.execute(SQL)
			conn.commit()
			data = cursor.fetchall()
			debug(data = data)
		if not data:
			print(make_colors("NO USERS !", 'lw', 'r'))
			return False
		n = 1
		if select:
			if str(select).isdigit():
				return data[int(select) - 1]
		if len(data) == 1:
			return data[0]

		for i in data:
			print(
				make_colors(self.format_number(n) + ".", 'lc') + " " + \
				make_colors(i[1], 'b', 'ly')
			)
		q = raw_input(make_colors("Select user:", 'b', 'lg') + " ")
		if q:
			if q.isdigit():
				if int(q) <= len(data):
					return data[int(q) - 1]
		return False

	@classmethod
	def usage(self):
		parser = argparse.ArgumentParser(description = 'Please becarefull ! :)')
		parser.add_argument('SOURCE_PATH', help = "Path scanning to", action = 'store')
		parser.add_argument('-p', '--path', help = 'Root repo path, default is: {}'.format(self.ROOT_REPO))
		if len(sys.argv) == 1:
			parser.print_help()
		else:
			args = parser.parse_args()
			if args.path:
				self.ROOT_REPO = args.path
			self.insert_db(args.SOURCE_PATH)

def usage():
	return Manage.usage()

if __name__ == '__main__':
	# repos = Manage.insert_db()
	Manage.usage()
	# Manage.user()
	# repos = Manage.make_db_config()