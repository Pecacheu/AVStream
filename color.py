import sys

class C:
	Rst='\x1b[0m' #Reset
	Br='\x1b[1m' #Bright
	Di='\x1b[2m' #Dim
	Un='\x1b[4m' #Underscore
	Bl='\x1b[5m' #Blink
	Rv='\x1b[7m' #Reverse

	Blk='\x1b[30m' #Black
	Red='\x1b[31m' #Red
	Grn='\x1b[32m' #Green
	Ylo='\x1b[33m' #Yellow
	Blu='\x1b[34m' #Blue
	Mag='\x1b[35m' #Magenta
	Cya='\x1b[36m' #Cyan
	Whi='\x1b[37m' #White

	BgBlk='\x1b[40m' #BgBlack
	BgRed='\x1b[41m' #BgRed
	BgGrn='\x1b[42m' #BgGreen
	BgYlo='\x1b[43m' #BgYellow
	BgBlu='\x1b[44m' #BgBlue
	BgMag='\x1b[45m' #BgMagenta
	BgCya='\x1b[46m' #BgCyan
	BgWhi='\x1b[47m' #BgWhite

def msg(*a):
	a=list(a); l=len(a)-1
	if(isinstance(a[l], str)): a[l]+=C.Rst+'\n'
	else: a.append(C.Rst+'\n')
	sys.stdout.write(' '.join(a))

def err(e,ex=0):
	sys.stderr.write(C.Red+e+C.Rst+'\n')
	if(ex): sys.exit(ex)