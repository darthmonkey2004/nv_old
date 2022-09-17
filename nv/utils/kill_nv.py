from os import kill
import psutil
from signal import SIGKILL

def get_pid():
	pid = None
	for proc in psutil.process_iter():
		if 'python3' in proc.name():
			for item in proc.cmdline():
				if 'bin/nv' in item:
					pid = proc.pid
	return pid


def kill_nv():
	try:
		pid = get_pid()
		if pid is not None:
			print(f"Killing nv at process id {pid}")
			kill(pid, SIGKILL)
			return True
		else:
			return False
	except Exception as e:
		print(f"Error killing process: {e}")
		return False
	
