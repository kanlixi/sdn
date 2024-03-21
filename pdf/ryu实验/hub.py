#实现集线器功能
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls



class Hub(app_manager.RyuApp):
    "集线器"

    OFP_VERSIONS=[ofproto_v1_3.OFP_VERSION]#openflow版本
    
    def __init__(self,*args,**kwargs):
        super(Hub,self).__init__(*args,**kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)#注册事件
    def switch_features_handler(self,ev):#处理交换机连接
        datapath=ev.msg.datapath#数据平面的通道,网桥
        ofproto = datapath.ofproto#版本
        ofp_parser = datapath.ofproto_parser
        #下发默认流表，上传到控制器上
        #install the table flow entry
        match=ofp_parser.OFPMatch()#匹配域
        actions=[ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                            ofproto.OFPCML_NO_BUFFER)]#发送入端口，buffer_id

        self.add_flow(datapath,0,match,actions)#默认流表项，将消息发送到控制器


    def add_flow(self,datapath,priority,match,actions):
        #add a flow entry and install it into datapath
        ofproto =datapath.ofproto
        ofp_parser =datapath.ofproto_parser

        #construct a flow_mod msg and send it
        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                            actions)]
        mod = ofp_parser.OFPFlowMod(datapath=datapath,priority=priority,match=match,instructions=inst)
        datapath.send_msg(mod)#发送消息





    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)#使用装饰器，监听
    def packet_in_handler(self,ev):#packet_in数据包进入，handler解决
        msg=ev.msg
        datapath =msg.datapath
        ofproto=datapath.ofproto
        ofp_parser = datapath.ofproto_parser #协议项的数据结构
        in_port = msg.match['in_port']#匹配域

        #instruct a flow entry
        match = ofp_parser.OFPMatch()
        actions =[ ofp_parser.OFPActionOutput(ofproto.OFPP_FLOOD) ]#把数据包发送到全部端口,泛洪（除了正在使用的端口）

        #install a flow mod to avoid packet_in next time
        self.add_flow(datapath,1,match,actions)


        #处理当下数据包
        out = ofp_parser.OFPPacketOut(datapath=datapath,buffer_id=msg.buffer_id,in_port=in_port,actions=actions)#buffer缓冲区，数据包存储

        datapath.send_msg(out)


