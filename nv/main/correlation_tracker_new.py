"""
@author: Mahmoud I.Zidan
"""

from dlib import correlation_tracker, rectangle
import nv

'''Appearance Model'''


class tracker():
	def __init__(self, _id, bbox, img, name=None, maxDisappeared=50):
		self.id = _id
		self.name = name
		self.img = img
		self.max_age = 300
		self.pos = bbox
		self.maxDisappeared = maxDisappeared
		self.tracker = correlation_tracker()
		self.l, self.t, self.r, self.b = bbox
		self.tracker.start_track(img,rectangle(int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])))
		self.confidence = 1
		self.time_since_update = 0
		self.age = 0




	def update(self, img, name=None):
		if name is not None:
			self.name = name
		self.time_since_update = 0
		self.confidence = self.tracker.update(img)
		self.pos = self.tracker.get_position()
		self.l, self.t, self.r, self.b = self.pos.left(), self.pos.top(), self.pos.right(), self.pos.bottom()
		out = (self.id, self.name, self.age, self.confidence, [self.l, self.t, self.r, self.b])
		return out

	def get_pos(self):
		self.age += 1
		pos = self.tracker.get_position()
		self.l, self.t, self.r, self.b = pos.left(), pos.top(), pos.right(), pos.bottom()
		out = (self.id, self.name, self.age, self.confidence, [self.l, self.t, self.r, self.b])
		return out

class tracker_mgr():
	global tracker
	def __init__(self):
		self.trackers = {}
		self.name = None
		self.img = None
		self.confidence = 0
		self.max_age = 300


	def ck_age(self, _id):
		t = self.trackers[_id]
		t.age += 1
		if t.age <= t.max_age:
			return True
		else:
			del self.trackers[_id]
			return False


	def new_tracker(self, bbox, img, name=None, maxDisappeared=50):
		names = []
		_id = None
		for _tid in list(self.trackers.keys()):
			if name == self.trackers[_tid].name:
				_id = _tid
		if _id is None:
			_id = len(list(self.trackers.keys())) + 1
		t = tracker(_id, bbox, img, name, maxDisappeared)
		_id = t.id
		self.trackers[_id] = t
		return t


	def rm_tracker(self, _id=None):
		try:
			if _id is None:
				_id = self.id
			del self.trackers[_id]
			return True
		except Exeption as e:
			return False

	def get_trackers(self):
		for _id in list(self.trackers.keys()):
			self.ck_age(_id)
		return self.trackers


	def get_tracker(self, _id):
		try:
			return trackers[_id]
		except Exception as e:
			return False

	def get_pos(self, _id):
		return self.trackers[_id].get_pos()


	def update_all(self, img):
		out = []
		for _id in list(self.trackers.keys()):
			ret = self.ck_age(_id)
			if ret:
				t = self.trackers[_id]
				out.append(t.update(img))
		return out
				

	def update(self, img, _id, name=None):
		t = self.trackers[_id]
		if name is not None:
			return t.update(img, name)
		else:
			return tracker.update(img)


	def get_tracker_object(self, _id):
		return self.trackers[_id]

	def list_ids(self):
		return list(self.trackers.keys())

	def get_data(self, _id):
		try:
			d  = {}
			t = self.trackers[_id]
			d['id'] = int(t.id)
			d['name'] = t.name
			d['name'] = t.max_age
			d['name'] = t.pos
			d['name'] = t.maxDisappeared
			d['name'] = t.l
			d['name'] = t.t
			d['name'] = t.r
			d['name'] = t.b
			d['name'] = t.confidence
			d['name'] = t.time_since_update
			d['name'] = t.age
			return d
		except:
			return None
