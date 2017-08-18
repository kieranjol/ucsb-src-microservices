#!/usr/bin/env python
import imp
import argparse
import getpass
import os
import subprocess
import csv
import re
import ast
import time
from distutils import spawn


#check that we have the required software to run this script
def dependencies():
	depends = ['bwfmetaedit','ffmpeg','ffprobe']
	for d in depends:
		if spawn.find_executable(d) is None:
			print "Buddy, you gotta install " + d
			sys.exit()
	return


#hashmove processing folder to the repo	
def move(rawfname,aNumber,captureDir,archRepoDir):
	if aNumber.endswith("A") or aNumber.endswith("B") or aNumber.endswith("C") or aNumber.endswith("D"):
		aNumber = aNumber[:-1]
	dirNumber = aNumber
	processingDir = os.path.join(captureDir,dirNumber)
	if os.path.isdir(processingDir):
		endDirThousand = aNumber.replace("a","") #input arg here is a1234 but we want just the number
		#the following separates out the first digit and assigns an appropriate number of zeroes to match our dir structure
		if len(endDirThousand) < 5:
			endDirThousand = endDirThousand[:1] + "000"
		else:
			endDirThousand = endDirThousand[:2] + "000"
		endDir = os.path.join(archRepoDir,endDirThousand,dirNumber)
		#hashmove it and grip the output so we can delete the raw files YEAHHH BOY
		output = subprocess.Popen(['python',os.path.join(conf.scriptRepo,'hashmove.py'),processingDir,endDir],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		foo,err = output.communicate()
		print foo
		sourcehash = re.search('srce\s\S+\s\w{32}',foo)
		desthash = re.search('dest\s\S+\s\w{32}',foo)
		dh = desthash.group()
		sh = sourcehash.group()
		bexttxt = os.path.join("R:/audio/avlab/fm-exports/bexttxts","cusb-" + dirNumber + "-bext.txt")
		startObj1 = os.path.join("R:/audio/avlab/fm-exports/to_process",rawfname + ".txt")
		if sh[-32:] == dh[-32:]:
			output = subprocess.Popen(['python',os.path.join(conf.scriptRepo,'hashmove.py'),os.path.join(captureDir,rawfname + ".wav"),endDir],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			foo,err = output.communicate()


def makefullffstr(ffstring,face,aNumber,channelConfig,processDir,rawfile): #takes the ffstring generated by fm-stuff and turns it into a full command for ffmpeg
	###INIT VARS###
	fullffstr = "ffmpeg -i " + rawfile + " " + ffstring
	endfileface = ''
	###END INIT###
	###SET END FILE FACE###
	if face == "fAB" and "Quarter Track Stereo" in channelConfig:
		endfileface = "A"
	elif face == "fCD" and "Quarter Track Stereo" in channelConfig:
		endfileface = "C"
	elif face == "fAB" and "Half Track Stereo" in channelConfig or "Full Track Mono" in channelConfig or "Cassette" in channelConfig:
		endfileface = ""	
	else:
		endfileface = face.replace("f","")
	###END END FILE FACE###
	###REPLACE FM-STUFF CHANNEL PLACEHOLDERS###
	if  "AB" in face:
		fullffstr = fullffstr.replace("left",os.path.join(processDir,"cusb-" + aNumber + "Aa")).replace("right",os.path.join(processDir,"cusb-" + aNumber + "Ba"))
	elif "CD" in face:
		fullffstr = fullffstr.replace("left",os.path.join(processDir,"cusb-" + aNumber + "Ca")).replace("right",os.path.join(processDir,"cusb-" + aNumber + "Da"))
	###END REPLACE###
	###GET IT TOGETHER###
	fullffstr = fullffstr.replace("processed",os.path.join(processDir,"cusb-" + aNumber + endfileface + "a"))
	return fullffstr

	
def ffprocess(fullffstr,processDir): #actually process with ffmpeg
	if not os.path.exists(processDir):
		os.makedirs(processDir) #actually make the processing directory
	time.sleep(1) #give the file table time to catch up
	###DO THE THING###
	with ut.cd(processDir):
		try:
			output = subprocess.check_output(fullffstr,shell=True)
			returncode = 0
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = output
	###END DOING THE THING###


def mono_silence(rawfname,face,aNumber,processDir): #silence removal for tapes that are mono
	#ffmpeg -af silenceremove works on the file level, not stream level
	with ut.cd(processDir):
		for f in os.listdir(os.getcwd()):#make a list of the whole directory contents
			if f.endswith(".wav"):#grip just wavs
				try:
					#silencedetect filter arguments are same order as on ffmpeg filters doc
					returncode = subprocess.check_output("ffmpeg -i " + f + " -af silenceremove=1:0:-60dB:-1:30:-60dB -c:a pcm_s24le -map 0 -threads 0 " + f.replace(".wav","") + "-silenced.wav")
					#CHECK_OUTPUT IS THE BEST
					returncode = 0
				except subprocess.CalledProcessError,e: #if there's an error, set the returncode to that
					returncode = e.returncode
				if returncode < 1: #if the returncode is not an error, we know that ffmepg was sucessful and that it's safe to delete the start file
					os.remove(os.path.join(processDir,f))
					os.rename(os.path.join(processDir,f.replace(".wav","-silenced.wav")),f)
	#NOTE FOR LATER
	#NEED TO RETURN THE RETURNCODE TO MAIN()
	

def reverse(rawfname,face,aNumber,channelConfig,processDir):#calls makereverse
	###INIT VARS###
	revface = subprocess.check_output(["python","fm-stuff.py","-pi","-t","-p","reverse","-so",rawfname,"-f",face,"-cc",channelConfig])
	###END INIT###
	###REVERSE FACE###
	if "fA" in revface and not "fAB" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Aa.wav")):
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Aa.wav")])
	elif "fC" in revface and not "fCD" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Ca.wav")):	
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Ca.wav")])	
	elif "fB" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Ba.wav")):	
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Ba.wav")])
	elif "fD" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Da.wav")):	
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Da.wav")])
	elif "fAB" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Aa.wav")):
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Aa.wav")])
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Ba.wav")):
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Ba.wav")])
		#sometimes the face isn't specified in the filename
		elif os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "a.wav")):
			print "2"
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "a.wav")])
	elif "fCD" in revface:
		if os.path.exists(os.path.join(processDir,"cusb-" + aNumber + "Ca.wav")):
			subprocess.check_output(['python',os.path.join(conf.scriptRepo,"makereverse.py"),'-so',os.path.join(processDir,"cusb-" + aNumber + "Ca.wav")])
	###END REVERSE FACE###

	
def sampleratenormalize(processDir):
	#ok so by now every file in the processing dir is the correct channel config & plays in correct direction BUT
	#we need to normalize to 96kHz
	#files with speed changes are currently set to 192000Hz or 48000Hz
	with ut.cd(processDir):
		for f in os.listdir(os.getcwd()): #for each file in the processing dir
			if f.endswith(".wav"):
				print "ffprobe and resample if necessary"
				#send ffprobe output to output.communicate()
				output = subprocess.Popen("ffprobe -show_streams -of flat " + f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				ffdata,err = output.communicate()
				###GET SAMPLE RATE###
				match = ''
				sr = ''
				match = re.search(r".*sample_rate=.*",ffdata)
				if match:
					_sr = match.group().split('"')[1::2]
					sr = _sr[0]
				###END GET SAMPLE RATE###
				###CONVERT SAMPLE RATE###
				if not sr == "96000":
					output = subprocess.call("ffmpeg -i " + f + " -ar 96000 -c:a pcm_s24le " + f.replace(".wav","") + "-resampled.wav")
					if os.path.getsize(f.replace(".wav","") + "-resampled.wav") > 50000:
						os.remove(os.path.join(os.getcwd(),f))
						time.sleep(1)
						os.rename(f.replace(".wav","") + "-resampled.wav",f) 
				###END CONVERT###

	
def makebext(aNumber,processDir): #embed bext info using bwfmetaedit
	try:
		kwargs = {"aNumber":aNumber,"bextVersion":"1"}
		bextstr = makemtd.makebext_complete(conf.magneticTape.cnxn,**kwargs)
	except:
		bextstr = "--originator=US,CUSB,SRC --originatorReference=" + aNumber.capitalize()
	with ut.cd(processDir):
		for f in os.listdir(os.getcwd()):
			if f.endswith(".wav"):
				subprocess.check_output("bwfmetaedit --in-core-remove " + f) #removes all bext info currently present
				print "embedding MD5 hash of data chunk..."
				subprocess.check_output("bwfmetaedit --MD5-Embed-Overwrite " + f) #embeds md5 hash of data chunk, overwrites if currently exists
				print "embedding BEXT chunk..."
				subprocess.check_output("bwfmetaedit " + bextstr + " " + f) #embeds bext v0 info

	
def main():
	###INIT VARS###
	dn, fn = os.path.split(os.path.abspath(__file__))
	global conf
	rawconfig = imp.load_source('config',os.path.join(dn,'config.py'))
	conf = rawconfig.config()
	global ut
	ut = imp.load_source("util",os.path.join(dn,"util.py"))
	global log
	log = imp.load_source('log',os.path.join(dn,'logger.py'))
	global makemtd
	makemtd = imp.load_source('makemtd',os.path.join(dn,'makemetadata.py'))
	parser = argparse.ArgumentParser(description="batch processes audio transfers")
	parser.add_argument('-s',dest='s',action="store_true",default=False,help='single mode, for processing a single transfer')
	parser.add_argument('-so','--startObj',dest='so',help="the rawcapture file.wav to process")
	args = parser.parse_args()
	captureDir = conf.magneticTape.new_ingest
	archRepoDir = conf.magneticTape.repo
	avlab = conf.magneticTape.avlab
	scratch = conf.magneticTape.scratch
	###END INIT###

	###SINGLE MODE###
	if args.s is True:
		###INIT###
		file = args.so
		rawfname,ext = os.path.splitext(file)
		###END INIT###
		###GET ANUMBER FACE AND CHANNELCONFIG FROM FILEMAKER###
		#output = subprocess.check_output(["python","fm-stuff.py","-pi","-t","-p","nameFormat","-so",rawfname]) #get aNumber, channelconfig, face from FileMaker
		kwargs = {"aNumber":args.so.capitalize()}
		acf = makemtd.get_aNumber_channelConfig_face(conf.magneticTape.cnxn,**kwargs)
		print acf
		foo = raw_input("eh")
		if processList is not None:
			print processList
			face = processList[0]
			aNumber = "a" + processList[1]
			channelConfig = processList[2]
			###END GET ANUMBER FACE CHANNELCONFIG FROM FILEMAKER###
			###DO THE FFMPEG###
			ffstring = subprocess.check_output(["python","fm-stuff.py","-pi","-t","-p","ffstring","-so",rawfname,"-f",face,"-cc",channelConfig])
			if ffstring is not None:
				#init folder to do the work in
				processDir = os.path.join(captureDir,aNumber)
				#make the full ffstr using the paths we have
				fullffstr = makefullffstr(ffstring,face,aNumber,channelConfig,processDir,os.path.join(captureDir,file))
				print fullffstr
				#run ffmpeg on the file and make sure it completes successfully
				returncode = ffprocess(fullffstr,processDir)
				#special add for mono files
				if "Mono" in channelConfig:
					mono_silence(rawfname,face,aNumber,processDir)	
				#if we need to reverse do it
				#note here to add output checker for reverse
				foo = raw_input("eh")
				reverse(rawfname,face,aNumber,channelConfig,processDir)
				#if we need to normalize our sample rate to 96kHz, because we sped up or slowed down a recording, do it here
				#note here to add output checker for reverse
				sampleratenormalize(processDir)
				###END THE FFMPEG###
				###EMBED BEXT###
				makebext(aNumber,processDir)
				#hashmove them to the repo dir
				move(rawfname,aNumber,captureDir,archRepoDir)
				###END BEXT###
	###END SINGLE MODE###
	###BATCH MODE###
	else:
		for dirs,subdirs,files in os.walk(captureDir):
			for file in files:
				###GET RID OF BS###
				if file.endswith(".gpk") or file.endswith(".mrk") or file.endswith(".bak") or file.endswith(".pkf"):
					try:
						os.remove(file)
					except:
						pass
				###END BS###
				###PROCESS CAPTURE###
				elif file.endswith(".wav"):
					try: #control for files currently in use
						subprocess.call("ffprobe " + os.path.join(dirs,file))
					except:
						continue
					###INIT###
					print file
					processNone = 0
					rawfname,ext = os.path.splitext(file)
					###END INIT###
					###GET ANUMBER FACE AND CHANNELCONFIG FROM FILEMAKER###
					output = subprocess.check_output(["python","fm-stuff.py","-pi","-t","-p","nameFormat","-so",rawfname])
					print output
					if not output.startswith("uh buddy"):
						processList = ast.literal_eval(output)
					else:
						continue
					if processList is not None:
						for p in processList:
							if p is None:
								processNone = 1
						if processNone > 0:
							break
						print processList
						face = processList[0]
						aNumber = "a" + processList[1]
						channelConfig = processList[2]
						###END GET ANUMBER FACE AND CHANNELCONFIG FROM FILEMAKER###
						###DO FFMPEG###
						ffstring = subprocess.check_output(["python","fm-stuff.py","-pi","-t","-p","ffstring","-so",rawfname,"-f",face,"-cc",channelConfig])
						if ffstring is not None:
							#init folder to do the work in
							processDir = os.path.join(captureDir,aNumber)
							#make the full ffstr using the paths we have
							fullffstr = makefullffstr(ffstring,face,aNumber,channelConfig,processDir,os.path.join(dirs,file))
							print fullffstr
							#run ffmpeg on the file and make sure it completes successfully
							ffprocess(fullffstr,processDir)
							#os.remove(os.path.join(captureDir,rawfname + ".wav"))
							#special add for mono files
							if "Mono" in channelConfig:
								mono_silence(rawfname,face,aNumber,processDir)
							#if we need to reverse do it
							#note here to add output checker for reverse
							reverse(rawfname,face,aNumber,channelConfig,processDir)
							#if we need to normalize our sample rate to 96kHz, because we sped up or slowed down a recording, do it here
							#note here to add output checker for reverse
							sampleratenormalize(processDir)
							###END FFMPEG###
							###EMBED BEXT###
							makebext(aNumber,processDir)
							###END BEXT###
							#hashmove them to the repo dir
							move(rawfname,aNumber,captureDir,archRepoDir)
							
				###END PROCESS CAPTURE###			
	###END BATCH MODE###						
dependencies()
main()
