#! /usr/bin/python3

import os
import re
import time
import argparse
import subprocess
import configparser
from argparse import RawTextHelpFormatter

EC_IO_FILE = '/sys/kernel/debug/ec/ec0/io'
PC_CODE_FILE = '/etc/pc_code'
CFG_FILE = '/etc/isw.conf'
CLISW_CFG_FILE = '/etc/clisw.conf'
VERSION = '1.1'

list_cpu_temp = []
list_cpu_fan_speed = []

list_gpu_temp = []
list_gpu_fan_speed = []


#Class used for argument -s, set cpu_fan_speed_0 quickly
class RunScript(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    pc_code = read_name()
    if pc_code is None:
      print("An error has occurred with isw config!")
      return None

    read_config(pc_code)
    
    address = list_cpu_fan_speed[0][1]

    if values == 'start':
      temperature = 45
    else:
      temperature = 0

    setattr(namespace, self.dest, values)
    bash = "isw -s "+str(address)+" "+str(temperature)
    subprocess.Popen(bash.split(),stdout=subprocess.DEVNULL)


def main():
  check_sudo() #it is necessary for read and write the operations

  parser = argparse.ArgumentParser(formatter_class = RawTextHelpFormatter)
  parser.add_argument("-s", action = RunScript, choices = ['start','stop'], 
                      help = 'Shortcut for set cpu_fan_speed_0:\n'
                              '|start -> 45\n'
                              '|stop -> 0')
  parser.add_argument("-v", action='store_const', const=1, help = 'clisw version')
  args = parser.parse_args()
  
  if args.v is not None:
    print("Clisw version: "+str(VERSION))
    return None
  elif args.s is not None:
    return None
  
  os.system('clear')
  print("Welcome to clisw\n")
  
  pc_code = read_name()
  if pc_code is None:
    print("An error has occurred with isw config!")
    return None
  print("This is your pc code: "+pc_code)

  read_config(pc_code) 
  
  parameter = ["0) Exit","1) Cpu","2) Gpu"]

  finish = False
  while not finish:
    print("Choose which parameter you want change:")
    for par in parameter:
      print(par)

    try:
      try:
        value = int(input("\nParameter: "))
      except ValueError:
        value = -1 

      if value >= 0 and value<len(parameter):
        if value == 0:
          finish = True
        elif value == 1:
         setting(list_cpu_fan_speed,list_cpu_temp,"cpu")
        elif value == 2:
          setting(list_gpu_fan_speed,list_gpu_temp,"gpu")      
      else:
        print("Wrong input. Try again!\n")
    except KeyboardInterrupt:
      print("\n")
      finish = True

  write_config(pc_code)

# check if the program has root privileges
def check_sudo():
  if os.geteuid() != 0:
    exit("[!] The program was not executed as root.\n[!] Please try again, this time using 'sudo'.")


# read the code of pc (i.e. for MSI PS63 8SC is 16S2EMS1)
def read_name():
  pc_code = read_name_file()
  
  if pc_code is None: #if there isn't file yet
    pc_code = read_name_ec()
    
    if pc_code is not None:
      with open(PC_CODE_FILE,"w") as temp:
        temp.write(pc_code)
          
  return pc_code

# read the pc code from pc_code file
def read_name_file():
  pc_code = None
  try:  
    with open(PC_CODE_FILE,"r") as temp:
      pc_code=temp.read()
  except:
    pass
  
  return pc_code

# read the code from EC file
def read_name_ec():
  ec = os.popen('od -A x -t x1z '+str(EC_IO_FILE)).read() #read ec

  if(ec == ''):
    return None

  ec_split = re.split("0000a0",ec) #split ec for read pc code
  ec_split1 = re.split("[><]", ec_split[1]) 
  pc_code =ec_split1[1].split(".")[0]

  return pc_code


def read_config(pc_code):
  file = CFG_FILE
  
  if(os.path.exists(CLISW_CFG_FILE)):
    file = CLISW_CFG_FILE

  with open(file) as cfgfile:
    cfgp = configparser.ConfigParser()
    cfgp.read_file(cfgfile)

    address_profile = cfgp.get(pc_code,"address_profile")
    
    for i in range(0,7):
      if i<6:
        cpu_temp = cfgp.get(pc_code,"cpu_temp_"+str(i))
        cpu_temp_add = cfgp.get(address_profile,"cpu_temp_address_"+str(i))
        list_cpu_temp.append([cpu_temp,cpu_temp_add])

        gpu_temp = cfgp.get(pc_code,"gpu_temp_"+str(i))
        gpu_temp_add = cfgp.get(address_profile,"gpu_temp_address_"+str(i))
        list_gpu_temp.append([gpu_temp,gpu_temp_add])

      cpu_value = cfgp.get(pc_code,"cpu_fan_speed_"+str(i))
      cpu_address = cfgp.get(address_profile,"cpu_fan_speed_address_"+str(i))
      list_cpu_fan_speed.append([cpu_value,cpu_address])

      gpu_value = cfgp.get(pc_code,"gpu_fan_speed_"+str(i))
      gpu_address = cfgp.get(address_profile,"gpu_fan_speed_address_"+str(i))
      list_gpu_fan_speed.append([gpu_value,gpu_address])


def setting(fan_speed_list,temp_list,component):
  parameter = ["0) Fan speed","1) Temperature","2) Go back"]
  
  finish = False

  while not finish:
    print("\nChoose which "+component+" parameter you want chage:")
    for i in parameter:
      print(i)

    try:
      value = int(input("\nParameter: "))
    except ValueError:
      value = -1 
    if value >= 0 and value<len(parameter):
      if value == 0:
        finish = fan_speed_settings(fan_speed_list,component)
      elif value == 1:
        finish = temp_setting(temp_list,component)
      else:
        finish = True
        print('')
    else:
      print("Wrong input. Try again!")


# Section for regulate the speed of the fans
def fan_speed_settings(fan_speed_list,component):
  len_list = len(fan_speed_list)

  i = 0
  for value in fan_speed_list:
    print(str(i)+") "+component+" fan speed "+str(i)+": "+str(value[0])+"\t "+str(value[1])) #print option
    i+=1
  print(str(len_list)+") Go back")

  ok = False
  go_back = False
  while not ok:
    try:
      index_value = int(input("\nInsert index of the value that you want edit: "))
    except ValueError:
      index_value = -1
    
    if index_value == len_list:
      ok = True
      go_back = True
      print('')
    elif index_value>-1 and index_value<len_list:
      while not ok:
        try:
          new_value = int(input("Insert value: "))
        except ValueError:
          new_value = -1
    
        if new_value>=0 and new_value<=100:
          ok = True
        else:
          print("\nWrong input. Insert a value between 0 and 100.\nTry again!\n")
    else:
      print("\nWrong input. Insert a index between 0 and "+str(len_list)+"\nTry again!")


  if not go_back:
    address = fan_speed_list[index_value][1]
    fan_speed_list[index_value][0] = str(new_value)
    # print("hai scelto "+str(address)+" col valore "+str(new_value)+"\n")
    bash = "isw -s "+str(address)+" "+str(new_value)
    subprocess.Popen(bash.split(),stdout=subprocess.DEVNULL)
    return True
  else: 
    return False


#Section for regulate the temperature
def temp_setting(temp_list,component):
  len_list = len(temp_list)

  i = 0
  for value in temp_list:
    print(str(i)+") "+component+" temp "+str(i)+": "+str(value[0])+"\t "+str(value[1])) #print option
    i+=1
  print(str(len_list)+") Go back")

  ok = False
  go_back = False
  while not ok:
    try:
      index_value = int(input("\nInsert index of the value that you want edit: "))
    except ValueError:
      index_value = -1

    if index_value == len_list:
      ok = True
      go_back = True
      print('')
    elif index_value>-1 and index_value<len_list:
      while not ok:
        try:
          new_value = int(input("Insert value: "))
        except ValueError:
          new_value = -1
          
        if new_value>=0 and new_value<=100:
          ok = True
        else:
          print("\nWrong input. Insert a value between 0 and 100.\nTry again!\n")
    else:
      print("\nWrong input. Insert a index between 0 and "+str(len_list)+"\nTry again!")

  if not go_back:
    address = temp_list[index_value][1]
    temp_list[index_value][0] = str(new_value)
    # print("hai scelto "+str(address)+" col valore "+str(new_value)+"\n")
    bash = "isw -s "+str(address)+" "+str(new_value)
    subprocess.Popen(bash.split(),stdout=subprocess.DEVNULL)
    return True
  else:
    return False


#Save the configuration
def write_config(pc_code):
  address_profile = 'address_profile'
  mad = 'MSI_ADDRESS_DEFAULT'

  cfgp = configparser.ConfigParser()
  cfgp[pc_code] = {}
  cfgp[mad] = {}
  
  cfgp[pc_code][address_profile] = mad

  create_configparser(cfgp,pc_code,'cpu_temp_',list_cpu_temp,0)
  create_configparser(cfgp,pc_code,'cpu_fan_speed_',list_cpu_fan_speed,0)
  create_configparser(cfgp,pc_code,'gpu_temp_',list_gpu_temp,0)
  create_configparser(cfgp,pc_code,'gpu_fan_speed_',list_gpu_fan_speed,0)

  create_configparser(cfgp,mad,'cpu_temp_address_',list_cpu_temp,1)
  create_configparser(cfgp,mad,'cpu_fan_speed_address_',list_cpu_fan_speed,1)
  create_configparser(cfgp,mad,'gpu_temp_address_',list_gpu_temp,1)
  create_configparser(cfgp,mad,'gpu_fan_speed_address_',list_gpu_fan_speed,1)

  with open(CLISW_CFG_FILE,'w') as test:
    cfgp.write(test)


def create_configparser(parser,pc_code,strn,list,pos):
  i=0
  for value in list:
    parser[pc_code][strn+str(i)] = value[pos]
    i=i+1

if __name__ == '__main__':
  main()
