import StellarPlayer
import json
import urllib
import os
from . import easywebdav

class webdevclientplugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.webdav = None
        self.dirlist_val = []
        self.filelist_val = []
        self.configjson = ''
        self.maindir = '/'
        self.server_ip = ''
        self.server_port = 80
        self.server_username = ''
        self.server_pwd = ''
        self.is_ssl = False
        
    def show(self):
        controls = self.makeLayout()
        self.doModal('main',800,700,'',controls)
    
    def start(self):
        super().start()
        self.configjson = self.player.dataDirectory + '\\config.json'
        if os.path.isfile(self.configjson):
            file = open(self.configjson, "rb")
            fileJson = json.loads(file.read())
            if fileJson:
                if 'ip' in fileJson:
                    self.server_ip = fileJson['ip']
                if 'port' in fileJson:
                    self.server_port = fileJson['port']
                if 'username' in fileJson:
                    self.server_username = fileJson['username']
                if 'password' in fileJson:
                    self.server_pwd = fileJson['password']
                if 'ssl' in fileJson:
                    self.is_ssl = fileJson['ssl']
    
    def makeLayout(self):
        dirlist_layout = {'group':[
                    {'type':'label','name':'dirname'}
                ]
            }
        filelist_layout = {'group':[
                    {'type':'label','name':'filename'}
                ]
            }
        controls = [
            {'group':
                [
                    {'type':'space','height':5},
                    {'type':'edit','name':'ip_edit','value':self.server_ip,'label':'主机(ip)','width':300,'height':25},
                    {'type':'space','height':5},
                    {'group':
                        [
                            {'type':'edit','name':'port_edit','value':str(self.server_port),'label':'端      口','width':150},
                            {'type':'space','width':50},
                            {'type':'check','name':'ssl','value':self.is_ssl}
                        ],
                        'height':25
                    },
                    {'type':'space','height':5},
                    {'type':'edit','name':'user_edit','value':self.server_username,'label':'用 户 名','width':300,'height':25},
                    {'type':'space','height':5},
                    {'group':
                        [
                            {'type':'edit','name':'pwd_edit','value':self.server_pwd, 'label':'密      码','width':300},
                            {'type':'space','width':50},
                            {'type':'button','name':'连接','width':60,'@click':'onConnect'},
                            {'type':'space','width':50},
                            {'type':'button','name':'保存','width':60,'@click':'onSave'},
                        ],
                        'height':25
                    }
                ],
                'dir':'vertical',
                'height':120
            },
            {'type':'space','height':5},
            {'group':
                [
                    {'type':'space','width':5},
                    {'type':'list','name':'dirlist','itemheight':30,'itemlayout':dirlist_layout,':value':'dirlist_val','width':0.3, '@dblclick': 'on_dirlist_item_dblclick', 'marginSize':20, 'separator': True},
                    {'type':'space','width':5},
                    {'type':'list','name':'filelist','itemheight':30,'itemlayout':filelist_layout,':value':'filelist_val','width':0.7, '@dblclick': 'on_filelist_item_dblclick', 'marginSize':20, 'separator': True},
                ]
            }
        ]
        return controls
        
    def onConnect(self,*args):
        self.server_ip = self.player.getControlValue('main','ip_edit').strip()
        self.server_port = int(self.player.getControlValue('main','port_edit'))
        self.server_username = self.player.getControlValue('main','user_edit').strip()
        self.server_pwd = self.player.getControlValue('main','pwd_edit').strip()
        self.is_ssl = self.player.getControlValue('main','ssl')
        if self.is_ssl:
            server_protocol = 'https'
        else:
            server_protocol = 'http'
        self.webdav = easywebdav.connect(self.server_ip, username = self.server_username, password = self.server_pwd, protocol = server_protocol, port = self.server_port)
        if self.webdav:
            self.maindir = '/'
            self.onLoadDir()
        else:
            self.player.toast('main','连接失败')
            
    def onSave(self,*args):
        jsondata = {}
        jsondata['ip'] = self.player.getControlValue('main','ip_edit').strip()
        strport = self.player.getControlValue('main','port_edit').strip()
        if strport == '':
            jsondata['port'] = 0
        else:
            jsondata['port'] = int(strport)
        jsondata['username'] = self.player.getControlValue('main','user_edit').strip()
        jsondata['password'] = self.player.getControlValue('main','pwd_edit').strip()
        jsondata['ssl'] = self.player.getControlValue('main','ssl')
        if os.path.exists(self.player.dataDirectory) == False:
            os.makedirs(self.player.dataDirectory) 
        with open(self.configjson,"w") as f:
            json.dump(jsondata,f,sort_keys=True, indent=4, separators=(',', ':'))
            
    def onLoadDir(self):
        self.loading()
        self.dirlist_val = []
        self.filelist_val = []
        files = self.webdav.ls(self.maindir)
        for file in files:
            checkfiles = self.webdav.ls(file.name)
            if len(checkfiles) > 1:
            #if file.contenttype.find('directory') >= 0:
                if file.name == self.maindir:
                    if self.maindir != '/':
                        pos = file.name.rfind("/")
                        path = file.name[:pos]
                        pos = path.rfind("/")
                        path = path[:pos]
                        if path == '':
                            path = '/'
                        self.dirlist_val.append({'dirname':'..','path':path})
                    else:
                        self.dirlist_val.append({'dirname':'..','path':'/'})
                else:
                    dirname = file.name.lstrip(self.maindir)
                    dirname = urllib.parse.unquote(dirname)
                    self.dirlist_val.append({'dirname':dirname,'path':file.name})
            else:
                filename = file.name.lstrip(self.maindir)
                filename = urllib.parse.unquote(filename)
                self.filelist_val.append({'filename':filename,'path':file.name})
        self.player.updateControlValue('main','dirlist',self.dirlist_val)
        self.player.updateControlValue('main','filelist',self.filelist_val)
        self.loading(True)
    
    def on_dirlist_item_dblclick(self, page, control, item):
        if self.webdav:
            dirpath = self.dirlist_val[item]['path']
            self.maindir = dirpath
            if dirpath[-1] != '/':
                self.maindir = self.maindir + '/'
            self.onLoadDir()
        else:
            self.player.toast('main','连接无效')
            
    def on_filelist_item_dblclick(self, page, control, item):
        playpath =  self.filelist_val[item]['path']
        if self.is_ssl:
            playurl = 'https://' 
        else:
            playurl = 'http://'
        playurl = playurl + self.server_username + ':' + self.server_pwd + '@' + self.server_ip + ':' + str(self.server_port) + playpath
        print(playurl)
        self.player.play(playurl)

    def loading(self, stopLoading = False):
        if hasattr(self.player,'loadingAnimation'):
            self.player.loadingAnimation('main', stop=stopLoading)
        
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = webdevclientplugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()