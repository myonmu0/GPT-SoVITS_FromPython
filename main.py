#!/usr/bin/env python3

import json
import requests
import re
import sys
import argparse
import random, string
import time
#import subprocess
import os
from playsound import playsound

abspath = os.path.abspath(__file__)
os.chdir(os.path.dirname(abspath))

SERVER_ADDR="0.0.0.0:9872"

null = None
gVoiceNum = 1

def text_to_speach(chat, cv_filename, cv_reference, addr, session_hash):
  print(chat)

  # Set GPT wight list
  r = requests.post(
  "http://" + addr + "/queue/join?",
  json={"data": [
      #"Use v2 base model directly without training!"
      "Use v3 base model directly without training!"
      ],
      "event_data": null,
      "fn_index": 3,
      "trigger_id": 5,
      "session_hash": session_hash,
	    },
  stream=False
  )
  if str(r.status_code) != "200":
    print(r.status_code)
    exit()

  # Set SoVITS weight list
  r = requests.post(
  "http://" + addr + "/queue/join?",
  json={"data": [
      #"Use v2 base model directly without training!",
      #"Use v2Pro base model directly without training!",
      "Use v2ProPlus base model directly without training!",
      "Japanese",
      "Japanese",
      ],
      "event_data": null,
      "fn_index": 2,
      "trigger_id": 6,
      "session_hash": session_hash,
	    },
  stream=False
  )
  if str(r.status_code) != "200":
    print(r.status_code)
    exit()

  # Upload reference audio
  r = requests.post("http://" + addr + "/upload", files=dict(files=open('cv/' + cv_filename, "rb")))
  remote_reference_file_path = json.loads(r.content)[0]
  requests.get("http://" + addr + "/queue/data?session_hash=" + session_hash)


  # Inference
  r = requests.post(
  "http://" + addr + "/queue/join?",
  json={"data": [
      {
          "path": remote_reference_file_path,
          "url": "http://" + addr + "/file=" + remote_reference_file_path,
          "orig_name": cv_filename,
          "size": 60204,
          "mime_type": "audio/mpeg",
          "meta": {
              "_type": "gradio.FileData"
          }
      },
      cv_reference,
      "Japanese",
      chat,
      "Japanese",
      "Slice once every 4 sentences",
      15,
      1,
      1,
      False,
      1,
      False,
      null,
      8,
      False,
      0.3
      ],
      "event_data": null,
      "fn_index": 1,
      "trigger_id": 47,
      "session_hash": session_hash,
	    },
  stream=False
  )
  if str(r.status_code) != "200":
    print(r.status_code)
    exit()

  # Get output file path
  r = requests.get("http://" + addr + "/queue/data?session_hash=" + session_hash)
  output_path = ""
  for l in r.text.split():
	    try:
	      json_data = json.loads(l)
	      output_path = json_data['output']['data'][0]['path']
	    except:
	      None
  
  # Get output file
  global gVoiceNum
  save_audio_path = "./output/"+ str(gVoiceNum) + ".wav"
  r = requests.get("http://" + addr + "/file=" + output_path)
  with open(save_audio_path, "wb") as f:
              f.write(r.content)
  gVoiceNum += 1
  playsound(save_audio_path)
  #subprocess.run(["mpv", "--loop=no", "--idle=no", "--loop-playlist=no", "--force-window=no", save_audio_path] ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
  return


def read_cv(cv):
  try:
    f = open("./cv/index.txt", "r")
    reference_list = f.read()
    f.close()
    for line in reference_list.splitlines():
      if line != "":
        cv_and_words  =  line.split(' ', 1)[0]
        
        if cv_and_words.split('.', 1)[0] == cv:
          cv_name = line.split(' ', 1)[0]
          cv_reference = line.split(' ', 1)[1]
          return([cv_name, cv_reference])
  except:
    print("./cv/index.txt is strange")
  return("Error")
      

def main():
    parser = argparse.ArgumentParser(description='Batch t2s')
    parser.add_argument('-i', '--input', help='Plot file.', required=True)
    parser.add_argument('-m', '--multi', help='Multi voice mode.', action='store_true')
    parser.add_argument('-v', '--voice', help='Single voice mode. Set character voice name here.')
    parser.add_argument('--ip', help='')
    parser.add_argument('--port', help='')

    args = parser.parse_args()
    story_file = args.input

    ip = args.ip
    port = args.port
    if ip != None and port != None:
      addr = ip + ":" + port
    else:
      addr = SERVER_ADDR

    if args.multi == False:
      if args.voice == None or args.voice == "":
        print("-voice required.")
        exit()

    # Generate session hash
    session_hash =  "1" + ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    
    # Single character mode
    if args.multi == False:
      cv_name, cv_reference = read_cv(args.voice)
      with open(story_file, "r") as f:
        for line in f.read().splitlines():
          convertToVoice(line, cv_name, cv_reference, addr, session_hash)

    # Multiple character mode
    else:
      # Check all available character
      available_characters = []
      with open("cv/index.txt", "r") as f:
        for line in f.read().splitlines():
         file_name = line.split(' ', 1)[0]
         character_name = file_name.split('.', 1)[0]
         available_characters.append(character_name)

      # Check if character name are valid
      chats = []
      with open(story_file, "r") as f:
        for line in f.read().splitlines():
          if line != "":
            available = False
            for c in available_characters:
              if re.match('^' + c + ' ', line):
                available = True
                break
            if available:
              chats.append(line)

      for chat in chats:
        cv = chat.split(' ', 1)[0]
        wd = chat.split(' ', 1)[1]
        
        cv_name, cv_reference = read_cv(cv)
        convertToVoice(wd, cv_name, cv_reference, addr, session_hash)

def convertToVoice(plot, cv_name, cv_reference, addr, session_hash):
  text_to_speach(plot, cv_name, cv_reference, addr, session_hash)
  print()


if __name__ == "__main__":
    main()
    
    
