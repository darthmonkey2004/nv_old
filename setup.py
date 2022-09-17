from setuptools import setup

setup(name='nv',
      version='0.1',
      description='Vision Package using dlib, opencv, PIL, ImageZMQ, and Flask (among others) to create a rtsp/webcam view/processing platform.',
      url='http://github.com/darthmonkey2004/nv',
      author='Matt McClellan',
      author_email='darthmonkey2004@gmail.com',
      license='GNU',
      packages=['nv', 'nv.oakdlite_fr'],
      package_dir={'nv': 'nv', 'nv.oakdlite_fr': 'oakdlite_fr'},
      scripts=['nv/scripts/scancams.sh'],
      )
