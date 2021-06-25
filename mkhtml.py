import nv

def browseLocal(webpageText, filename='tempBrowseLocal.html'):
    '''Start your webbrowser on a local file containing the text
    with given filename.'''
    import webbrowser, os.path
    strToFile(webpageText, filename)
    webbrowser.open("file:///" + os.path.abspath(filename)) #elaborated for Mac

def fileToStr(fileName): # NEW
    """Return a string containing the contents of the named file."""
    fin = open(fileName); 
    contents = fin.read();  
    fin.close() 
    return contents
title="CAMVIEWER"
w_px = "640px"
h_px = "480px"
#contents = fileToStr('index.html').format(**locals())
#browseLocal(contents)
#exit()


html = '''
<!doctype html>
<html lang="en">
<head>
	<title>{title}</title>
	<style type="text/css">
	.mover '''.format(**locals())
html2 = """ {
		 width:640px; height:480px; line-height:4em; margin:10px; padding:5px; float:left; border:1px dotted #333333; text-align:center;
			 }"""
html = (html + html2)
for cam_id in list(nv.CAMERAS.keys()):
	js_camsBlock1='''
			 #box_{cam_id}'''.format(**locals())
	js_camsBlock2="""{
				background-image: url("""
	js_camsBlock3="""{{ url_for('video_feed', id='"""
	js_camsBlock4='''{cam_id}'''.format(**locals())
	js_camsBlock5="""') }}"""
	js_camsBlock6=""")
			 }
"""
	js_camsBlock = (js_camsBlock1 + js_camsBlock2 + js_camsBlock3 + js_camsBlock4 + js_camsBlock5 + js_camsBlock6)
	html = (html + js_camsBlock)
html2 = """


	</style>
	<script type="text/javascript">
		function dragWord(dragEvent){
			dragEvent.dataTransfer.setData("Id",	dragEvent.target.id+"|"+dragEvent.target.parentNode.id);
			}				   
		function dropWord(dropEvent){ 
			var dropData = dropEvent.dataTransfer.getData("Id");
			dropItems = dropData.split("|"); 
			var prevElem = document.getElementById(dropItems[1]); 
			prevElem.getElementsByTagName("div")[0].id = dropEvent.target.id;			  
			dropEvent.target.id = dropItems[0]; 
			dropEvent.preventDefault(); 
			} 
	</script> 
	</head> 
	<body>
		<div id="camsection">
"""
html = (html + html2)
for cam_id in list(nv.CAMERAS.keys()):
	html_camsBlock='''
			<div id="box{cam_id}" ondragover="event.preventDefault()" ondrop="dropWord(event)">
			<div class="mover" id="box_{cam_id}" draggable="true" ondragstart="dragWord(event)"></div> 
			</div>
'''.format(**locals())
	html = (html + html_camsBlock)
html = (html + '''
		</div>
	</body> 
</html>''')
fn=(nv.EXEC_DIR + nv.sep + "templates" + nv.sep + "index.html")
f = open(fn, 'w')
f.write(html)
exit()
