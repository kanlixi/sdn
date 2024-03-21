#实现集线器功能
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls



#定义一个类hub，继承app_manager，位于ryu下的base内，
#版本选择openflow1.3，然后初始化操作。
class Hub(app_manager.RyuApp):
    "集线器"

    OFP_VERSIONS=[ofproto_v1_3.OFP_VERSION]#openflow版本
    
    def __init__(self,*args,**kwargs):
        super(Hub,self).__init__(*args,**kwargs)


#接下来，需要定义packet in函数，用来处理交换机和控制器的流表交互，
#在执行之前需要先对packetin事件进行监听。
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



#ryu的数据平面是由若干网元（Network Element）组成，每个网元包含一个或
#多个SDN数据路径（SDN Datapath）.SDN Datapath是逻辑上的网络设备，负责转发
#和处理数据无控制能力，一个SDN DataPath包含控制数据平面接口
#（Control Data Plane Interface,CDPI）、代理、转发引擎（Forwarding Engine）表
#和处理功能（Processing Function）SDN数据面（转发面）的关键技术:对数据面进行抽象建模。
#对于添加流表，可以将其单独拿出了写一个函数。
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
        ofp_parser = datapath.ofproto_parser #协议项的数据结构
        in_port = msg.match['in_port']#匹配域

        #instruct a flow entry
        match = ofp_parser.OFPMatch()
        actions =[ ofp_parser.OFPActionOutput(ofproto.OFPP_FLOOD) ]
        #把数据包发送到全部端口,泛洪（除了正在使用的端口）

        #install a flow mod to avoid packet_in next time
        self.add_flow(datapath,1,match,actions)


        #处理当下数据包
        out = ofp_parser.OFPPacketOut(datapath=datapath,buffer_id=msg.buffer_id,
                                        in_port=in_port,actions=actions)
                                        #buffer缓冲区，数据包存储

        datapath.send_msg(out)


