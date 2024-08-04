def get_minutes(time):
	if time[-1] == 'h':
		minutes = int(time[:-1]) * 60 # hours
	elif time[-1] == 'm':
		minutes = int(time[:-1])
	return minutes