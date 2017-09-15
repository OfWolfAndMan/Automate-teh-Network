from jinja2 import Environment, FileSystemLoader
ENV = Environment(loader=FileSystemLoader('.'))
template = ENV.get_template("L2int.j2")

class L2Interface(object):
	def __init__(self, description, vlan, voice=False, voice_vlan=20, uplink=False, intname="GigabitEthernet"):
		self.intname = intname
		#self.intnum = intnum
		self.description = description
		self.vlan = vlan
		self.voice = voice
		self.voice_vlan = voice_vlan
		self.uplink = uplink

interface_object = L2Interface("<==Server Port==>", 30, voice=True)

print(template.render(interface=interface_object)).strip('\n\r')
