#AVStream ©2023 Pecacheu. GNU GPL v3.0
import os
import platform
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import re
import signal
import string
from threading import Thread
import subprocess as SP
import time
import json
from color import C,msg,err
VER="v0.3"

#------------------------------ Constants ------------------------------

#-c:a aac -b:a 128k -ac 2
WRITE_BUF = 16000; KILL_TIMEOUT = 10
LIST_CMD = "ffmpeg -hide_banner -list_devices true -f {0} -i dummy"
FMAT_CMD = "ffmpeg -hide_banner -f {0} -list_options true -i {1}"
STREAM_CMD = "ffmpeg -hide_banner -f {0} -i {1} -framerate {2} -video_size {3} \
-c:v libvpx-vp9 -g {2} -b:v 500k -f webm pipe:1"

# "ffmpeg -hide_banner -f {0} -i {1} -framerate {2} -video_size {3} \
# -c:v libx264 -crf 21 -preset veryfast -g {2} -sc_threshold 0 \
# -f ismv -movflags faststart pipe:1"

# "ffmpeg -hide_banner -f {0} -i {1} -framerate {2} -video_size {3} \
# -filter_complex \"[0:v]split=2[v1][v2]; [v1]copy[v1out]; [v2]scale=w=640:h=360[v2out]\" \
# -map [v1out] -c:v:0 libx264 -x264-params \"nal-hrd=cbr:force-cfr=1\" -b:v:0 5M -maxrate:v:0 5M -minrate:v:0 5M -bufsize:v:0 10M -preset slow -g 48 -sc_threshold 0 -keyint_min 48 \
# -map [v2out] -c:v:2 libx264 -x264-params \"nal-hrd=cbr:force-cfr=1\" -b:v:2 1M -maxrate:v:2 1M -minrate:v:2 1M \
# -bufsize:v:2 1M -preset slow -g 48 -sc_threshold 0 -keyint_min 48 \
# -map a:0 -c:a:0 aac -b:a:0 96k -ac 2 \
# -map a:0 -c:a:1 aac -b:a:1 96k -ac 2 \
# -f hls -hls_time 2 -hls_list_size 3 \
# -hls_flags independent_segments -hls_segment_type mpegts \
# -hls_segment_filename stream_%v/data%02d.ts \
# -master_pl_name master.m3u8 \
# -var_stream_map \"v:0,a:0 v:1,a:1\" stream_%v.m3u8"

#------------------------------ Helper Functions ------------------------------

class AttrDict(dict):
	def __init__(self, *args, **kwargs):
		super(AttrDict, self).__init__(*args, **kwargs)
		self.__dict__ = self

def readFile(fn, raw=False):
	with open(fn,raw and 'rb' or 'r') as f:
		s=f.read()
	return s

def readConfig(fn):
	with open(fn,'r') as f:
		d=AttrDict(json.load(f))
	return d

def runCmd(cmd, raw=False):
	global RC
	RC=SP.Popen(cmd, shell=True, stdout=SP.PIPE, stderr=SP.PIPE, text=not raw)

def killCmd():
	global RC, RS
	if(RC is None): return
	os.kill(RC.pid, signal.SIGINT); RC.wait(KILL_TIMEOUT)
	if(RC.poll() is None):
		msg("FFMPEG timed out! Forcing..."); RC.kill()
	RC=None; RS=None

#------------------------------ A/V Management ------------------------------

def getFormat():
	s=platform.system()
	match s:
		case "Windows": s="dshow" #TODO: Support Linux/Mac OS?
		case "Linux": s="v4l2"
		case _: raise "Unknown OS "+s
	return s

SPat=r'^\d+x\d+$'
def runStream():
	global RS
	v=VD and f"video=\"{VD}\":" or ""; a=AD and f"audio=\"{AD}\"" or ""
	f=CONF.fps; s=CONF.vidSize
	try:
		if(int(f) <= 0): raise ValueError
	except: raise "Invalid fps"
	if(not s or not re.fullmatch(SPat,s)): raise "Invalid size format"
	cmd=STREAM_CMD.format(getFormat(),v+a,f,s)
	msg("RUN_CMD:",cmd)
	runCmd(cmd, True)
	RS=True

def getDevices():
	global RC
	runCmd(LIST_CMD.format(getFormat()))
	_,stderr=RC.communicate(); RC=None
	if(not stderr.endswith("exit requested\n")):
		err("Error: "+stderr)
		return []
	else:
		dr=stderr.split('\n'); dl=[]
		for d in dr:
			if(not d.startswith('[')): continue
			try: dl.append(d[d.index(']')+2:d.rindex(')')+1])
			except ValueError: pass
		return dl

def filterStr(s):
	p=set(string.printable)
	return ''.join(filter(lambda s: s in p, s))

#------------------------------ HTTP Handling ------------------------------

class HttpHandler(BaseHTTPRequestHandler):
	def writeRes(self, code, res, noType=False):
		self.send_response(code, code != 200 and res or None)
		if(not noType): self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(isinstance(res,bytes) and res or bytes(res,'utf8'))

	def do_GET(self):
		if(self.path == '/sys'): self.writeRes(200, platform.node())
		elif(self.path == '/'): self.writeRes(200, readFile("index.html"))
		elif(self.path == '/live.webm'):
			if(RS):
				self.writeRes(500, "Stream Running")
			else:
				runStream()
				if(RC.poll() is None):
					self.send_response(200)
					#self.send_header("Transfer-Encoding", "chunked")
					self.end_headers()
					try:
						while(1):
							d=RC.stdout.read(WRITE_BUF)
							msg("Got "+str(len(d)))
							#self.wfile.write(bytes(f"{len(d):x}\r\n",'utf8'))
							self.wfile.write(d)
							time.sleep(0)
					except Exception as e:
						err(str(e))
						killCmd()
				else:
					self.writeRes(500, "Dead Stream")
		# elif(self.path.startswith('/stream/')):
		# 	try:
		# 		fc=readFile(self.path[1:], True)
		# 		self.writeRes(200, fc, True)
		# 	except FileNotFoundError:
		# 		self.writeRes(404, "Not Found")
		# 	except Exception as e:
		# 		err(f"Error for {self.path}: "+str(e))
		# 		self.writeRes(500, "Unknown Error")
		else: self.writeRes(404, "Not Found")

def runLoop():
	global Run
	try:
		while(Run):
			# if(RS == 1):
			# 	if(RC.poll() is None):
			# 		d=RC.stdout.read(WRITE_BUF)
			# 		msg("Temp Got "+str(len(d)))
			# 		time.sleep(0)
			# 	else:
			# 		Run=False
			# else:
			time.sleep(0.5)
	except KeyboardInterrupt:
		Run=False

def runReader():
	global Run
	while(Run):
		try:
			if(RS):
				s=str(RC.stderr.readline(),'utf8')
				if(s): msg(C.Blu+s)
				time.sleep(0)
			else: time.sleep(1)
		except KeyboardInterrupt:
			Run=False
		except Exception as e:
			err(str(e))

def runServer():
	global Run
	Run=True; addr=('', 8080)
	srv=ThreadingHTTPServer(addr, HttpHandler)
	ts=Thread(target=srv.serve_forever); ts.start()
	rs=Thread(target=runReader); rs.start()
	msg(C.Mag+"Ready!")
	runLoop()
	msg(C.Mag+"Exiting"); Run=False
	srv.shutdown(); ts.join(); rs.join()
	killCmd()

#------------------------------ Main Flow ------------------------------

#Read Config
msg(C.Br+C.Cya+"AVStream "+C.Ylo+VER)
try:
	CONF=readConfig("config.json")
	msg(str(CONF))
except Exception as e:
	err("Could not read config: "+str(e),1)

def findDev(dl,n):
	for d in dl:
		if(n == filterStr(d)): return d

#Check Devices
dev=getDevices(); pDev=0
if(not len(dev)):
	err("No A/V Devices Found!",2)

VD=findDev(dev, f"\"{CONF.vidDevice}\" (video)")
if(VD): VD=VD[1:-9]
else:
	err(f"Warning: Video Device '{CONF.vidDevice}' not found.")
	VD=''; pDev=pDev+1

AD=findDev(dev, f"\"{CONF.audDevice}\" (audio)")
if(AD): AD=AD[1:-9]
else:
	err(f"Warning: Audio Device '{CONF.vidDevice}' not found.")
	AD=''; pDev=pDev+1

if(pDev > 1):
	msg("Available Devices:")
	for d in dev: msg(C.Br+C.Blu+"- "+C.Ylo+filterStr(d))
	err("Please choose a video and/or audio device and add it to config.json.",3)

if(not re.fullmatch(SPat,CONF.vidSize) or not CONF.fps or not CONF.aRate):
	v=VD and f"video=\"{VD}\":" or ""; a=AD and f"audio=\"{AD}\"" or ""
	c=FMAT_CMD.format(getFormat(),v+a)
	msg(c)
	runCmd(c)
	_,stderr=RC.communicate()
	msg("Available Formats:\n"+C.Ylo+stderr[:-1])
	err("Please add desired format to config.json.",4)

#TODO: Show available formats if you use 'lf' as parameter
#TODO: Use aRate

#IDX_PAGE = readFile("index.html")
RS=0
runServer()