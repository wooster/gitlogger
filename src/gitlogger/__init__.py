import biplist
import json
import os 
from pbs import git
from pygithub3 import Github
import sys

HELP_MESSAGE = '''
gitlogger [action] [options]
	actions and their options
		help			Prints this message.
		add_user		Adds a user
			username password email_address
		add_email		Adds an email address to a user
			username email_address
		update_user		Updates the repos for the given user.
			username
		commits			Shows the commits for the given user.
			username
'''

class Usage(Exception):
	def __init__(self, msg):
		super(Usage, self).__init__(msg)
		self.msg = msg

def help_msg():
	print >> sys.stderr, HELP_MESSAGE

def actual_path(path):
	try:
		path = os.path.abspath(os.path.expanduser(path))
	except AttributeError:
		path = None
	return path

class Gitlogger(object):
	def __init__(self, storage_path='~/gitlogger_store'):
		self._setup_path(storage_path)
		self.user_file_path = os.path.join(self.storage_path, 'users.plist')
		if not os.path.exists(self.user_file_path):
			biplist.writePlist({}, self.user_file_path)
	
	def add_user(self, username, password):
		users = biplist.readPlist(self.user_file_path)
		users[username] = {'password':password, 'email_addresses':[]}
		if not os.path.exists(self._user_path(username)):
			os.mkdir(self._user_path(username))
		biplist.writePlist(users, self.user_file_path)
	
	def add_email(self, username, email):
		users = biplist.readPlist(self.user_file_path)
		user_info = users.get(username)
		if email not in user_info['email_addresses']:
			user_info['email_addresses'].append(email)
		users[username] = user_info
		biplist.writePlist(users, self.user_file_path)
	
	def checkout_repositories_for_user(self, username):
		userinfo = biplist.readPlist(self.user_file_path)
		repos = github_repos(username=username, password=userinfo[username]['password'])
		for repo in repos:
			print "Checking out: %s" % repo.name
			repo_path = self._repo_path(username, repo.name)
			if not os.path.exists(repo_path):
				self._clone_repo_in_path(repo, self._user_path(username))
			else:
				self._update_repo_in_path(repo, self._user_path(username))
	
	def commits_for_user(self, username):
		users = biplist.readPlist(self.user_file_path)
		user_info = users.get(username)
		email_addresses = user_info['email_addresses']
		in_user_commit = False
		current_timestamp = 0
		commits_for_timestamp = {}
		repos = github_repos(username=username, password=user_info['password'])
		for repo in repos:
			repo_path = self._repo_path(username, repo.name)
			log_for_repo = self._log_for_repo(repo, repo_path)
			for line in log_for_repo.splitlines():
				if line.startswith(">>"):
					(commit, timestamp, email) = line[2:].split()
					if email in email_addresses:
						in_user_commit = True
						current_timestamp = timestamp
						commits_for_timestamp.setdefault(current_timestamp, {'added':0, 'removed':0})
					else:
						in_user_commit = False
					continue
				elif len(line) and in_user_commit:
					try:
						(added, removed) = line.split()[0:2]
						if added != '-':
							commits_for_timestamp[timestamp]['added'] += int(added)
						if removed != '-':
							commits_for_timestamp[timestamp]['removed'] += int(removed)
					except ValueError as e:
						print >> sys.stderr, e
						print >> sys.stderr, "Error on:", line
		return commits_for_timestamp
	
	def _log_for_repo(self, repo, path):
		cwd = os.getcwd()
		os.chdir(path)
		output = git("--no-pager", "log", "--no-merges", "--numstat", pretty="format:>>%H %ct %aE")
		os.chdir(cwd)
		return output
	
	def _clone_repo_in_path(self, repo, path):
		cwd = os.getcwd()
		os.chdir(path)
		git.clone(repo.git_url)
		os.chdir(cwd)
	
	def _update_repo_in_path(self, repo, path):
		cwd = os.getcwd()
		os.chdir(os.path.join(path, repo.name))
		git.update()
		os.chdir(cwd)
	
	def _user_path(self, username):
		return os.path.join(self.storage_path, username)
	
	def _repo_path(self, username, project_name):
		return os.path.join(self._user_path(username), project_name)
	
	def _setup_path(self, storage_path):
		"""Initializes the data store."""
		storage_path = actual_path(storage_path)
		if not storage_path:
			raise Exception("Storage path is None")
		if not os.path.exists(storage_path):
			os.mkdir(storage_path)
		self.storage_path = storage_path
	

def github_repos(username=None, password=None):
	gh = Github(login=username, password=password)
	repos = gh.repos.list(username)
	return [repo for repo in repos.iterator()]

def main():
	argv = sys.argv
	try:
		if len(argv) < 2:
			raise Usage("No action given.")
		action = argv[1]
		if action == "help":
			help_msg()
		elif action == "add_user":
			username = argv[2]
			password = argv[3]
			email = None
			if len(argv) >= 5:
				email = argv[4]
			logger = Gitlogger()
			logger.add_user(username, password)
			logger.add_email(username, email)
		elif action == "add_email":
			username = argv[2]
			email = argv[3]
			logger = Gitlogger()
			logger.add_email(username, email)
		elif action == "update_user":
			username = argv[2]
			logger = Gitlogger()
			logger.checkout_repositories_for_user(username)
		elif action == "commits":
			username = argv[2]
			logger = Gitlogger()
			commits = logger.commits_for_user(username)
			print json.dumps(commits, indent=4)
		else:
			raise Usage("Unknown action given: %s" % action)
	except Usage as err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use help action"
		print >> sys.stderr, HELP_MESSAGE
		return 2
