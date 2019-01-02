from picamera import PiCamera
import threading

class RepeatTimer(threading.Thread):
	def __init__(self, interval, callable, *args, **kwargs):
		threading.Thread.__init__(self)
		self.interval = interval
		self.callable = callable
		self.args = args
		self.kwargs = kwargs
		self.status = False
		self.event = threading.Event()
		self.event.set()

	def start(self):
		self.status = True
		super(RepeatTimer, self).start()

	def run(self):
		while self.event.is_set():
			t = threading.Timer(self.interval, self.callable, self.args, self.kwargs)
			t.start()
			t.join()
			
	def set_interval(self, new_interval):
		self.interval = new_interval

	def cancel(self):
		self.status = False
		self.event.clear()


class TimelapseCamera(PiCamera):
	def __init__(self, interval=1, frameFilePath=".", startingFrameIndex=0, frameResolution=(1280,720)):
		self.myInterval = interval
		self.myFilePath = frameFilePath
		self.frameIndex = startingFrameIndex
		
		super(TimelapseCamera,self).__init__(resolution=frameResolution)
						
		self.myTimer = RepeatTimer(self.myInterval, self.capture_frame)
		return;

	def setFrameFilePath(self, frameFilePath):
		self.myFilePath = frameFilePath
		return;
		
	def setInterval(self, interval):
		self.myInterval = interval
		self.myTimer.set_interval(interval)
		return;
		
	def capture_frame(self):
		print self.capture_frame
		if self.myTimer.status == True:
			super(TimelapseCamera,self).capture(self.myFilePath + "/image{0:08d}.jpg".format(self.frameIndex) )
			self.frameIndex += 1
			return;
	
	def getFrameIndex(self):
		return self.frameIndex
		
	def start(self):
		self.myTimer.start()
		
	def stop(self):
		self.myTimer.cancel()