from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class ExampleSwitch(app_manager.RyuApp)
    OFP_VERSIONS=[ofproto_v1_3.OFP_VERSION]
    
    def __init__(self,*args,**kwargs):
        super(ExampleSwitch,self).__init__(*args,**kwargs)
        self.mac_to_port={}
        


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
    #注册事件
    def switch_features_handler(self,ev):#处理交换机连接

    # 这几句是对数据结构进行解析，是一种固定的形式，可以记住就行
        datapath=ev.msg.datapath#数据平面的通道,网桥
        ofproto = datapath.ofproto#版本
        ofp_parser = datapath.ofproto_parser
       
        #install the table flow entry
        match=ofp_parser.OFPMatch()#匹配域
        actions=[ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                            ofproto.OFPCML_NO_BUFFER)]
                                            #发送入端口，buffer_id

        self.add_flow(datapath,0,match,actions)
        #默认流表项，将消息发送到控制器

    def add_flow(self,datapath,priority,match,actions):
        #add a flow entry and install it into datapath
        ofproto =datapath.ofproto
        ofp_parser =datapath.ofproto_parser

        #construct a flow_mod msg and send it
        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                            actions)]
        mod = ofp_parser.OFPFlowMod(datapath=datapath,priority=priority,
                                    match=match,instructions=inst)
        datapath.send_msg(mod)#发送消息



    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)#使用装饰器，监听
    def packet_in_handler(self,ev):#packet_in数据包进入，handler解决
        msg=ev.msg
        datapath =msg.datapath
        ofproto=datapath.ofproto
        ofp_parser = datapath.ofproto_parser #解析模块
        
        #自学习算法
        #1.得到datapath id to identyfy openflow switch 
        #dpid也就是datapath id
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid,{})

        #save the info
        #parser and analylize the received packets
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)#eth以太网,以太网数据包
        dst = eth_pkt.dst
        src = eth_pkt.src
        in_port = msg.match['in_port']
        self.logger.info('packet in %s %s %s %s',dpid,src,dst,in_port)#打印消息

        #learn the src mac address to avoid FLOOD next time
        self.mac_to_port[dpid][src] =in_port


        #if the dst mac address has already learned 
        #decide which port to send packets
        #otherwise flood
        
        if dst in self.mac_to_port[dpid]:
            out_port=self.mac_to_port[dpid][dst]
        else :
            out_port = ofproto.OFPP_FLOOD
        
        #contract actions
        actions = [ofp_parser.OFPActionOutput(out_port)]

        #install a flow mod msg
        if out_port != ofproto.OFPP_FLOOD:
            match = ofp_parser.OFPMatch(in_port=in_port,eth_dst = dst) 
            self.add_flow(datapath,1,match,actions)

        #send a packet out
        out = ofp_parser.OFPPacketOut(
            datapath=datapath,buffer_id=msg.buffer_id,in_port=in_port,
            actions=actions)

        datapath.send_msg(out)
        
        
        
    