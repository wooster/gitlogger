from pygithub3 import Github
import biplist
import os 

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
			biplist.writePlist({'users':{}}, self.user_file_path)
	
	def add_user(self, username, password):
		users = biplist.readPlist(self.user_file_path)
		users[username] = {'password':password}
		if not os.path.exists(self._user_path(username)):
			os.path.mkdir(self._user_path(username))
		biplist.writePlist(users, self.user_file_path)
	
	def checkout_repositories_for_user(self, username):
		userinfo = biplist.readPlist(self.user_file_path)
		repos = github_repos(username=username, userinfo['username']['password'])
		for repo in repos:
			repo_path = self._repo_path(username, repo.name)
			if not os.path.exists(repo_path):
				self._clone_repo_in_path(repo, self._user_path())
			else:
				self._update_repo_in_path(repo, self._user_path())
	
	def _clone_repo_in_path(repo, path):
		pass
	
	def _update_repo_in_path(repo, path):
		pass
	
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
			os.path.mkdir(storage_path)
		self.storage_path = storage_path
	

def github_repos(username=None, password=None):
	gh = Github(login=username, password=password)
	repos = gh.repos.list(username)
	return [repo.clone_url for repo in repos.iterator()]

def main():
	logger = Gitlogger()
    print "Hello World"
