from setuptools import setup

setup(name='muot',
	version='0.12',
	description='App for the TFG, Area of Security',
	url='http://github.com/sergioln/muot',
	author='Sergio Lucas',
	author_email='sergio.ln@gmail.com',
	packages=['muot'],
	install_requires[
		'tweepy',
		'osrframework',
		'elasticsearch']
	zip_safe=False)
