from pygithub3 import Github

def github_repo_clone_urls(username=None, password=None):
	gh = Github(login=username, password=password)
	repos = gh.repos.list(username)
	return [repo.clone_url for repo in repos.iterator()]

def main():
    print "Hello World"



