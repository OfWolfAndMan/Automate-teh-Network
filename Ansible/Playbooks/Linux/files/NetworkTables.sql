CREATE TABLE network_inventory(
   Hostname varchar(50),
   Model varchar(50),
   Serial varchar(20),
   Portnum int,
   Software varchar(20)
);

CREATE TABLE vlan_database(
   Vid int,
   Iface varchar(20),
   Enabled varchar(5),
   Descr varchar(20),
   Psec varchar (5) 
);

CREATE TABLE network_interfaces(
   Hostname varchar(20),
   Interface varchar(20),
   IP_Address inet,
   Protocol_Status varchar(5),
   Status varchar(5)
);
