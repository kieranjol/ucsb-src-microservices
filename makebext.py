#makebext

#coding=UTF-8
import os
import sys
import shutil
import time
import argparse
import ConfigParser
import getpass

def main():	
	#initialize all of the things
	#initialize arguments coming in from cli
	parser = argparse.ArgumentParser()
	#parser.add_argument('-cyl','--cylinder',action='store_true',dest='cyl',default=False,help="make metadata file using cylinder template")
	parser.add_argument('-tape','--magneticTape',action='store_true',dest='tape',default=False,help="make metadata file using cylinder template")
	#parser.add_argument('-disc','--disc',action='store_true',dest='disc',default=False,help="make metadata file using disc template")
	parser.add_argument('-so','--startObj',dest='so',help="the asset that we want to make metadata for")
	parser.add_argument('-d','--date',dest='m',default="",help="'mastered' from FM, the date this asset was digitized")	
	parser.add_argument('-mk','--masterKey',dest='mk',default="",help="5 digit number linking the file to a physical object in FM")
	parser.add_argument('-t','--title',dest='t',default="",help="the title of the object in FM")
	parser.add_argument('-mss','--mss',dest='mss',default="",help="the collection number/code of the object")
	parser.add_argument('-c','--collection',dest='c',default="",help="the collection name of the object")
	args = parser.parse_args()
	config = ConfigParser.ConfigParser()
	config.read("C:/Users/" + getpass.getuser() + "/microservices-config.ini")
	
	if args.tape is True: #for tapes do this
		archiveDir = config.get("magneticTape","magTapeArchDir") #grab archive directory for audio tapes
		endDirThousand = args.so.replace("a","") #input arg here is a1234 but we want just the number
		#the following separates out the first digit and assigns an appropriate number of zeroes to match our dir structure
		if len(endDirThousand) < 5:
			endDirThousand = endDirThousand[:1] + "000"
		else:
			endDirThousand = endDirThousand[:2] + "000"
		startDir = os.path.join(archiveDir,endDirThousand,args.so) #booshh
		if not os.path.isdir(startDir): #again, if it doesn't exists let's not chase it
			print "Buddy, this tape hasn't been digitized yet"
			print "When it is digitized we'll worry about making ID3 tags for it"
			foo = raw_input("Press any key to quit")
			sys.exit()
		mtdObj = os.path.join(startDir,"cusb-" + args.so + "-bext.txt") #init a metadata object
		originator = "US,CUSB,SRC"
		originatorRef = "cusb-" + args.so
		description = 
	
	
	return

mai()