for k in opts.keys():
	val = opts[k]
	if type(val) != dict:
		string = f"opts['{k}'] = '{val}'"
		print(string)
	else:
		e = '{}'
		print(f"opts['{k}'] = {e}")
		for k2 in val.keys():
			val2 = opts[k][k2]
			if type(val2) != dict:
				print(f"opts['{k}']['{k2}'] = '{val2}'")
			else:
				print(f"opts['{k}']['{k2}'] = {e}")
				for k3 in val2.keys():
					val3 = opts[k][k2][k3]
					if type(val3) != dict:
						print(f"opts['{k}']['{k2}']['{k3}'] =  '{val3}'")
					else:
						print (f"opts['{k}']['{k2}']['{k3}'] = {e}")
						for k4 in val3.keys():
							val4 = opts[k][k2][k3][k4]
							if type(val4) != dict:
								print(f"opts['{k}']['{k2}']['{k3}']['{k4}'] = '{val4}'")
							else:
								print(k4, val4)
								input()
