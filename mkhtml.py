import nv
import sqlite3

conn = sqlite3.connect(nv.SQLDB)
cur = conn.cursor()
cur.execute("SELECT camera_id, src, src_dims, feed, ptz FROM cams")
rows = cur.fetchall()
CAMERAS = {}
FEEDS = {}
PTZS = {}
DIMS = {}
for row in rows:
	camera_id, src, src_dims, feed, ptz = row
	CAMERAS[camera_id] = src
	FEEDS[camera_id] = feed
	PTZS[camera_id] = ptz
	DIMS[camera_id] = src_dims

title="CAMVIEWER"
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
		 line-height:4em; margin:10px; padding:5px; float:left; border:1px dotted #333333; text-align:center;
			 }"""
#TODO html3 = '''width:640px; height:{}px; '''.format(**locals())
html = (html + html2)
for cam_id in list(CAMERAS.keys()):
	js_camsBlock1='''
			 #box_{cam_id}'''.format(**locals())
	js_camsBlock2="""{
				"""
	dims= (DIMS[cam_id])
	h = dims.split(',')[0].split('(')[1]
	w = dims.split(' ')[1].split(')')[0]
	print (w, h)
	js_camsBlock3='''width:{w}px; height:{h}px; '''.format(**locals())
	js_camsBlock4="""background-image: url("""
	js_camsBlock5="""{{ url_for('video_feed', id='"""
	js_camsBlock6='''{cam_id}'''.format(**locals())
	js_camsBlock7="""') }}"""
	js_camsBlock8=""")
			 }
"""
	js_camsBlock = (js_camsBlock1 + js_camsBlock2 + js_camsBlock3 + js_camsBlock4 + js_camsBlock5 + js_camsBlock6 + js_camsBlock7 + js_camsBlock8)
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
for cam_id in list(CAMERAS.keys()):
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
