import base64
import gzip
import socket
import time

class DFTemplate:
    def __init__(self):
        self.commands = []
        self.closebracket = None

    def build(self):
        main_dict = {'blocks': []}
        for cmd in self.commands:
            main_dict['blocks'].append({
                'args': {
                    'items': []
                    }
                })
            
            # add keys from cmd.data
            for key in cmd.data.keys():
                main_dict['blocks'][-1][key] = cmd.data[key]

            # bracket data
            if cmd.data.get('direct') != None:
                main_dict['blocks'][-1]['direct'] = cmd.data['direct']
                main_dict['blocks'][-1]['type'] = cmd.data['type']
            
            # add target if necessary
            if cmd.data.get('block') != 'event':
                if cmd.target != 'Default':
                    main_dict['blocks'][-1]['target'] = cmd.target
            

            # add items into args part of dictionary
            slot = 0
            if cmd.args:  # tuple isnt empty
                for arg in cmd.args[0]:
                    app = None
                    if arg.type in {'txt', 'num', 'item', 'loc', 'var'}:
                        app = arg.format(slot)
                        main_dict['blocks'][-1]['args']['items'].append(app)
                
                    slot += 1
        

        print('Template Built Successfully!')
        print(main_dict)

        try:
            templateName = main_dict['blocks'][0]['block'] + '_' + main_dict['blocks'][0]['action']
        except KeyError:
            templateName = main_dict['blocks'][0]['data']
        
        return self._compress(str(main_dict)), templateName
    
    def buildAndSend(self):
        built, templateName = self.build()
        self.sendToDF(built,name=templateName)
    
    def _compress(self, string):
        comp_string = gzip.compress(string.encode('utf-8'))
        return str(base64.b64encode(comp_string))[2:-1]
    
    # send template to diamondfire
    # test what it sends back when client is offline so that i can write a proper error message
    def sendToDF(self,code,name='None'):
        data = {"type":"template","source":f"dfpy - {name}","data":f"{{\"name\":\"dfpy Template - {name}\",\"data\":\"{code}\"}}"}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1',31372))
        s.send((str(data)+'\n').encode())
        
        received = s.recv(1024)
        print(received.decode())
        s.close()
        time.sleep(0.5)
    
    def _convertDataTypes(self,lst):
        retList = []
        for element in lst:
            if type(element) in {int, float}:
                retList.append(num(element))
            elif type(element) == str:
                retList.append(text(element))
            else:
                retList.append(element)
        return tuple(retList)
    
    def clear(self):
        self.commands = []
    
    def _openbracket(self,btype='norm'):
        bracket = Command('Bracket',data={'id': 'bracket', 'direct': 'open', 'type': btype})
        self.commands.append(bracket)
        self.closebracket = btype
    
    # command methods
    def player_event(self,name):
        cmd = Command(name,data={'id': 'block', 'block': 'event', 'action': name})
        self.commands.append(cmd)
    
    def entity_event(self,name):
        cmd = Command(name,data={'id': 'block', 'block': 'entity_event', 'action': name})
        self.commands.append(cmd)
    
    def function(self,name):
        cmd = Command('function',data={'id': 'block', 'block': 'func', 'data': name})
        self.commands.append(cmd)
    
    def process(self,name):
        cmd = Command('process',data={'id': 'block', 'block': 'process', 'data': name})
        self.commands.append(cmd)
    
    def call_function(self,name,parameters={}):
        if parameters:
            for key in parameters.keys():
                self.set_var('=',var(key,scope='local'),parameters[key])
        
        cmd = Command('call_func',data={'id': 'block', 'block': 'call_func', 'data': name})
        self.commands.append(cmd)
    
    def start_process(self,name):
        cmd = Command('start_process',data={'id': 'block', 'block': 'start_process', 'data': name})
        self.commands.append(cmd)

    def player_action(self,name,*args,target='Default'):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,target=target,data={'id': 'block', 'block': 'player_action', 'action': name})
        self.commands.append(cmd)
    
    def game_action(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'game_action', 'action': name})
        self.commands.append(cmd)
    
    def entity_action(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'entity_action', 'action': name})
        self.commands.append(cmd)
    
    def if_player(self,name,*args,target='Default'):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,target=target,data={'id': 'block', 'block': 'if_player', 'action': name})
        self.commands.append(cmd)
        self._openbracket()
    
    def if_variable(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'if_var', 'action': '='})
        self.commands.append(cmd)
        self._openbracket()
    
    def if_game(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'if_game', 'action': name})
        self.commands.append(cmd)
        self._openbracket()
    
    def if_entity(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'if_entity', 'action': name})
        self.commands.append(cmd)
        self._openbracket()

    def else_(self,*args):
        cmd = Command('else',data={'id': 'block', 'block': 'else'})
        self.commands.append(cmd)
        self._openbracket()
    
    def repeat(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'repeat', 'action': name})
        self.commands.append(cmd)
        self._openbracket('repeat')

    def bracket(self,*args):
        args = self._convertDataTypes(args)
        cmd = Command('Bracket',data={'id': 'bracket', 'direct': 'close', 'type': self.closebracket})  # close bracket
        self.commands.append(cmd)
    
    def control(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'control', 'action': name})
        self.commands.append(cmd)
    
    def select_object(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'select_obj', 'action': name})
        self.commands.append(cmd)
    
    def set_var(self,name,*args):
        args = self._convertDataTypes(args)
        cmd = Command(name,args,data={'id': 'block', 'block': 'set_var', 'action': name})
        self.commands.append(cmd)


# command class
class Command:
    def __init__(self,name,*args,target='Default',data={}):
        self.name = name
        self.args = args
        self.target = target
        self.data = data


# df item classes (will add particle, sound, game value later)
class item:
    def __init__(self,itemID,count=1):
        self.id = itemID
        self.count = count
        self.type = 'item'
    
    def format(self,slot):
        return dict({
            "item": {
              "id": "item",
              "data": {
                "item": f"{{DF_NBT:2586,id:\"{self.id}\",Count:{self.count}b}}"
              }
            },
            "slot": slot
          })

class text:
    def __init__(self,string):
        self.value = string
        self.type = 'txt'
    
    def format(self,slot):
        return dict({
              "item": {
                "id": "txt",
                "data": {
                  "name": self.value
                }
              },
              "slot": slot
            })

class num:
    def __init__(self,num):
        self.value = num
        self.type = 'num'
    
    def format(self,slot):
        return dict({
            "item": {
              "id": "num",
              "data": {
                "name": str(self.value)
              }
            },
            "slot": slot
          })

class loc:
    def __init__(self,x=0,y=0,z=0,pitch=0,yaw=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.type = 'loc'
    
    def format(self,slot):
        return dict({
            "item": {
              "id": "loc",
              "data": {
                "isBlock": False,
                "loc": {
                  "x": self.x,
                  "y": self.y,
                  "z": self.z,
                  "pitch": self.pitch,
                  "yaw": self.yaw
                }
              }
            },
            "slot": slot
          })

class var():
    def __init__(self,name,scope='unsaved'):
        if scope == 'game':
            scope = 'unsaved'
        
        self.name = name
        self.scope = scope
        self.type = 'var'

    def format(self,slot):
        return dict({
            "item": {
              "id": "var",
              "data": {
                "name": self.name,
                "scope": self.scope
              }
            },
            "slot": slot
          })