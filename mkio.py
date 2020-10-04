#This file is for use in STCustom's NicVision, part of the cross platform "Nicole" package, which is still a work in progress.
#Use this module to write detected objects and faces to a temporary python script file which can be read in without conversion on the fly.
#This module is used by NicVision to create the IO files that determine whether the NicVision.display module shows just the captured image, or creates an overlay with bounding boxes on the image; dependant on whether or not any data is included in the 'data' list object
#Feel free to modify, change, adapt, or just generally use this file as you see fit. It's all open source anyway, right?
def mkIOFile(list_object, iofile_name = "temp"):#define function to export list or tuple
	try:#enclosed in a try/except block just in case the iterable test fails it doesn't throw an exception and kill your code
		if hasattr(list_object, "__iter__") == True:# test to see if object is iterable. By default, lists and tuples are, string objects are not.
			cont = 1#for debug purposes
		else:
			cont = 0
			return ("Type doesn't appear to be a list or tuple. You can just write this to file normally.")
		#This code block below is where the magic happens. It writes a function into a text file(name of file stored in iofile_name) containing the list you passed to this function earlier.
		outstring = ("def showlist():" + '\n' + "	newlist = " + str(list_object) + '\n' + "	return (newlist)" + '\n')
		fname = (iofile_name + ".py")# set the file name to a .py extension to enable python's import function.
		out = open(fname, "w")#open the file for writing
		out.write(outstring)#write the prepared file contents.
		out.close() #close the file
		outstr = ("IO Object written at '" + fname + "'!")
		return(outstr)#return success
	except:
		return ("Unhandled exception, did not pass the try except catch block.")#handle exception

