
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.ofproto import ether
from ryu.lib.packet import ether_types, ipv4, icmp, arp
import joblib
import numpy as np
import asyncio
import websockets
import json
from websockets.sync.client import connect

# from ryu.ofproto.ofproto_v1_3_parser import OFPFeaturesRequest

import datetime

# * RyuApp class should be inherited to define a RYU application
class SimpleSwitch13(app_manager.RyuApp):
    
    # * Openflow version 1.3 should be used
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        
        # * initialize mac address table
        self.mac_to_port = {}
        
        # self.ml_model = joblib.load('model.pkl')
        # self.le_proto = joblib.load('proto.joblib')
        # self.le_label = joblib.load('label.joblib')
        # self.sc = joblib.load("scaler.joblib")
        self.host = 'localhost'
        self.port = 8765
        self.totalPacketsIn = 0
        
    
    def send_websocket_message(self, message):
        with connect("ws://localhost:8765") as websocket:
            websocket.send(message)
            message = websocket.recv()
            print(f"Received: {message}")

    # * define event handler functions using decorators, event class name is ryu.controller.ofp_event.EventOFP + <OpenFlow message name>. For example, in case of a Packet-In message, it becomes EventOFPPacketIn
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        print("New switch: ", datapath.id)

        # * attributes of datapath instance, it stores the feature information about the switch 
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        
        # * this code tells the switch to send all the packets directly to the controller without buffering
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions) # * this line adds the flow entry to the switch

    # * add flow method makes flow entries inside a switch with instructionss
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)


    # * packet in handler will handle the packet once the packet is sent to controller by the switch
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.totalPacketsIn += 1
        print(self.totalPacketsIn)
        # * If you hit this you might want to increase the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # * analysing the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        # self.analyze_flows(datapath, pkt)

        # if eth.ethertype == ether_types.ETH_TYPE_IPV6:
        #     return
        
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        
        # * set the value to defailt if dpid doesn't exist
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s %s", dpid, src, dst, in_port, datetime.datetime.now().isoformat())
        self.send_websocket_message(f"packet in {dpid} {src} {dst} {in_port} {datetime.datetime.now().isoformat()}")

        # * learn a mac address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # * install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
                
        # * sending the packet from switch        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    # # * Analyze flows
    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def flow_stats_reply_handler(self, ev):
    #     self.logger.info("Flow stats reply received")
    #     flow_stats = ev.msg.body
    #     self.logger.info("Found {} flows".format(len(flow_stats)))
    #     flow_info = {}
    #     active_hosts = set()

    #     for stat in flow_stats:
    #         match = stat.match
    #         if match is None:
    #             continue

    #         nw_proto = match.get('nw_proto')
    #         nw_src = match.get('nw_src')
    #         nw_dst = match.get('nw_dst')
    #         tp_src = match.get('tp_src')
    #         tp_dst = match.get('tp_dst')
    #         packet_count = stat.packet_count
    #     pass

    # def get_flow_duration(self, flow_stats):
    #     duration_sec = flow_stats.get('duration_sec', 0)
    #     duration_nsec = flow_stats.get('duration_nsec', 0)
    #     return duration_sec + duration_nsec / 1e9

    # def get_average_packet_size(self, flow_stats):
    #     packet_count = flow_stats.get('packet_count', 0)
    #     byte_count = flow_stats.get('byte_count', 0)
    #     return byte_count / packet_count if packet_count != 0 else 0