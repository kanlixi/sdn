from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,DEAD_DISPATCHER
from ryu.lib import hub

class  MyMonitor13(simple_switch_13.SimpleSwitch13):
    #监控网络流量
    #string for description

    def __init__(self,*args,**kwargs):
        super(MyMonitor13,self).__init__(*args,**kwargs)
        self.datapaths={}
        self.monitor_thread = hub.spawn(self._monitor)


    #get datapath info
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER,DEAD_DISPATCHER])#注册事件，监听        
    def _state_change_handler(self,ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:#交换机上线
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
                self.logger.debug("Register datapath: %16x",datapath.id )


        elif ev.state == DEAD_DISPATCHER:#交换机下线
            if datapath.id in self.datapaths:
                self.logger.debug("UnRegister datapath : %16x",datapath.id)                       
                del self.datapaths[datapath.id] 
        
    #send request msg periodically
    #主动下发调用消息
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)#请求报文发送给datapath
                
            #休眠
            hub.sleep(10)


    #send stats request msg to datapath
    def _request_stats(self,datapath):
           
        ofproto =datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        #send port stats request msg
        #端口项；主动下发信息
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        #send flow stats request msg
        #流表项；主动下发信息
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        self.logger.debug("send stats request to datapath:%16x",datapath.id)

        

        
    #被动下发消息
    #handle the port stats reply msg
    @set_ev_cls(ofp_event.EventOFPPortStatsReply,MAIN_DISPATCHER)
    def _port_stats_reply_handler(self,ev):#监听事件ev触发
        body = ev.msg.body
        #统计消息解析
        self.logger.info('datapath                    port       '
                            'rx-pkts      rx-bytes   rx-errors  '
                            'tx-pkts      tx-bytes   tx-errors  ')
        self.logger.info('---------------------   ----------'
                            '----------  ----------  ----------'
                            '----------  ----------  ----------')
        for stat in sorted(body,key=attrgetter('port_no')):
            self.logger.info("%16x %8x %8d %8d %8d %8d %8d %8d",
                            ev.msg.datapath.id,stat.port_no,
                            stat.rx_packets,stat.rx_bytes,stats.rx_errors,
                            stat.tx_packets,stat.tx_bytes,stat.tx_errors)



    #handle the flow entry stats reply msg
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply,MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self,ev):
        body = ev.msg.body
        self.logger.info('datapath                           '
                            'in_port            eth-dst         '
                            'out_port     packets      bytes    ')
        self.logger.info('----------------------------'
                            '----------    --------- -----------'
                            '----------  ----------  ----------')
        for stat in sorted([flow for flow in body if flow.priority==1],
                            key=lambda flow : (flow.match['in_port'],
                                                flow.match['eth_dst'])):
            self.logger.info("%16x %8x %8d %8d %8d %8d %8d %8d",
                            ev.msg.datapath.id,
                            stat.match['in_port'],stat.match['eth_dst'],
                            stats.instructions[0],actions[0],port,
                            stat.packet_count,stat.byte_count)