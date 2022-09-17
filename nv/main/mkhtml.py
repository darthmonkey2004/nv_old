def mkhtml(cams, camera_id):
	print (cams)
	all_html = []
	title = "Camera{camera_id}"
	html=f"""<!doctype html>
<html lang="en">
	<head>
		<title>{title}</title>
	</head> 
	<body>
		<div class="camsection" id="camsection">
"""
	all_html.append(html)
	for camera_id in list(cams.keys()):
		src = cams[camera_id]['url']
		block=f"""			<div id="cam{camera_id}">
			 <img id="{camera_id}" src="{src}" alt="Camera {camera_id}" width="{cams[camera_id]['w']}" height="{cams[camera_id]['h']}"> 
			  <script src="motionjpeg.js"></script>
			  <script>
			  	$(document).ready(function() """'{'f"""
			  		motionjpeg("#{camera_id}");
			  	"""'}'""";
			  </script>
			</div>
"""
		all_html.append(block)
	html="""
		</div>
	</body> 
</html>
"""
	all_html.append(html)
	j="\n"
	return j.join(all_html)

if __name__ == "__main__":
	print (mkhtml())

