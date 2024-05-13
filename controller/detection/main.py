from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.lib.packet import ipv4
import switch
from datetime import datetime, timedelta

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

SERVICE_TYPES = {
    0: 'eco_i',
    21: 'FTP',       # File Transfer Protocol (FTP)
    22: 'SSH',       # Secure Shell (SSH)
    23: 'Telnet',    # Telnet
    25: 'SMTP',      # Simple Mail Transfer Protocol (SMTP)
    53: 'DNS',       # Domain Name System (DNS)
    80: 'HTTP',      # Hypertext Transfer Protocol (HTTP)
    110: 'POP3',     # Post Office Protocol version 3 (POP3)
    123: 'NTP',      # Network Time Protocol (NTP)
    143: 'IMAP',     # Internet Message Access Protocol (IMAP)
    443: 'HTTPS',    # HTTP Secure (HTTPS)
    3306: 'MySQL',   # MySQL Database Server
    3389: 'RDP',
    8080: 'http'# Remote Desktop Protocol (RDP)
}

class SimpleMonitor13(switch.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        self.PROTOCOL_NAME = {1 : 'icmp', 6 : 'tcp', 17 : 'udp'}
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)
            print("Predict flow!")
            # self.flow_predict()

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        timestamp = datetime.now()
        timestamp = timestamp.timestamp()

        # file0 = open("PredictFlowStatsfile.csv","w")
        print('timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
        body = ev.msg.body
        icmp_code = -1
        icmp_type = -1
        tp_src = 0
        tp_dst = 0

        flows = {}
        counts = {}
        srv_counts = {}
        for stat in sorted([flow for flow in body if (flow.priority == 1) ], key=lambda flow:
            (flow.match['eth_type'],flow.match['ipv4_src'],flow.match['ipv4_dst'],flow.match['ip_proto'])):
        
            ip_src = stat.match['ipv4_src']
            ip_dst = stat.match['ipv4_dst']
            ip_proto = stat.match['ip_proto']
            
            # * it is an icmp packet
            if stat.match['ip_proto'] == 1:
                icmp_code = stat.match['icmpv4_code']
                icmp_type = stat.match['icmpv4_type']
            
            # * it is a tcp packet
            elif stat.match['ip_proto'] == 6:
                tp_src = stat.match['tcp_src']
                tp_dst = stat.match['tcp_dst']

            # * it is a udp packet
            elif stat.match['ip_proto'] == 17:
                tp_src = stat.match['udp_src']
                tp_dst = stat.match['udp_dst']
            
            else:
                continue
            
            protocol_type = self.PROTOCOL_NAME[ip_proto]
            duration = stat.duration_sec
            if tp_dst in SERVICE_TYPES:
                service = SERVICE_TYPES[tp_dst]
            else:
                service = 'private'            
            
            if (ip_src, ip_dst, protocol_type) not in flows:
                flows[(ip_src, ip_dst, protocol_type)] = {}
                flows[(ip_src, ip_dst, protocol_type)]['bytes'] = 0
                
            flows[(ip_src, ip_dst, protocol_type)]['bytes'] += stat.byte_count
            flows[(ip_src, ip_dst, protocol_type)]['duration'] = duration
            flows[(ip_src, ip_dst, protocol_type)]['service'] = service
                
            if ip_dst in counts:
                counts[ip_dst].append(datetime.now())
            else:
                counts[ip_dst] = [datetime.now()]
                
            if tp_dst in srv_counts:
                srv_counts[tp_dst].append(datetime.now())
            else:
                srv_counts[tp_dst] = [datetime.now()]
                

            flow_id = str(ip_src) + str(tp_src) + str(ip_dst) + str(tp_dst) + str(ip_proto)
          
            try:
                packet_count_per_second = stat.packet_count/stat.duration_sec
                packet_count_per_nsecond = stat.packet_count/stat.duration_nsec
            except:
                packet_count_per_second = 0
                packet_count_per_nsecond = 0
                
            try:
                byte_count_per_second = stat.byte_count/stat.duration_sec
                byte_count_per_nsecond = stat.byte_count/stat.duration_nsec
            except:
                byte_count_per_second = 0
                byte_count_per_nsecond = 0
                
            print("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n"
                .format(timestamp, ev.msg.datapath.id, flow_id, ip_src, tp_src,ip_dst, tp_dst,
                        stat.match['ip_proto'],icmp_code,icmp_type,
                        stat.duration_sec, stat.duration_nsec,
                        stat.idle_timeout, stat.hard_timeout,
                        stat.flags, stat.packet_count,stat.byte_count,
                        packet_count_per_second,packet_count_per_nsecond,
                        byte_count_per_second,byte_count_per_nsecond))
            
        stats = []
        current_time = datetime.now()
        for key, value in flows.items():
            stat = {}
            stat['duration'] = value['duration']
            stat['service'] = value['service']
            stat['protocol_type'] = key[2]
            stat['src_bytes'] = value['bytes']
            if flows[(key[1], key[0], protocol_type)]:
                stat['dst_bytes'] = flows[(key[1], key[0], protocol_type)]['bytes']
            else:
                stat['dst_bytes'] = 0
            stat['count'] = sum(1 for ts in counts[ip_dst] if (current_time - ts) < timedelta(seconds=2))
            stat['srv_count'] = sum(1 for ts in srv_counts[tp_dst] if (current_time - ts) < timedelta(seconds=2))
            stats.append(stat)
        self.logger.info(stats)
        # file0.close()

    # def flow_training(self):

    #     self.logger.info("Flow Training ...")

    #     flow_dataset = pd.read_csv('FlowStatsfile.csv')

    #     flow_dataset.iloc[:, 2] = flow_dataset.iloc[:, 2].str.replace('.', '')
    #     flow_dataset.iloc[:, 3] = flow_dataset.iloc[:, 3].str.replace('.', '')
    #     flow_dataset.iloc[:, 5] = flow_dataset.iloc[:, 5].str.replace('.', '')

    #     X_flow = flow_dataset.iloc[:, :-1].values
    #     X_flow = X_flow.astype('float64')

    #     y_flow = flow_dataset.iloc[:, -1].values

    #     X_flow_train, X_flow_test, y_flow_train, y_flow_test = train_test_split(X_flow, y_flow, test_size=0.25, random_state=0)

    #     classifier = RandomForestClassifier(n_estimators=10, criterion="entropy", random_state=0)
    #     self.flow_model = classifier.fit(X_flow_train, y_flow_train)

    #     y_flow_pred = self.flow_model.predict(X_flow_test)

    #     self.logger.info("------------------------------------------------------------------------------")

    #     self.logger.info("confusion matrix")
    #     cm = confusion_matrix(y_flow_test, y_flow_pred)
    #     self.logger.info(cm)

    #     acc = accuracy_score(y_flow_test, y_flow_pred)

    #     self.logger.info("succes accuracy = {0:.2f} %".format(acc*100))
    #     fail = 1.0 - acc
    #     self.logger.info("fail accuracy = {0:.2f} %".format(fail*100))
    #     self.logger.info("------------------------------------------------------------------------------")

    def flow_predict(self):
        try:
            predict_flow_dataset = pd.read_csv('PredictFlowStatsfile.csv')

            predict_flow_dataset.iloc[:, 2] = predict_flow_dataset.iloc[:, 2].str.replace('.', '')
            predict_flow_dataset.iloc[:, 3] = predict_flow_dataset.iloc[:, 3].str.replace('.', '')
            predict_flow_dataset.iloc[:, 5] = predict_flow_dataset.iloc[:, 5].str.replace('.', '')

            X_predict_flow = predict_flow_dataset.iloc[:, :].values
            X_predict_flow = X_predict_flow.astype('float64')
            
            y_flow_pred = self.flow_model.predict(X_predict_flow)

            legitimate_trafic = 0
            ddos_trafic = 0

            for i in y_flow_pred:
                if i == 0:
                    legitimate_trafic = legitimate_trafic + 1
                else:
                    ddos_trafic = ddos_trafic + 1
                    victim = int(predict_flow_dataset.iloc[i, 5])%20
                    
                    
                    

            self.logger.info("------------------------------------------------------------------------------")
            if (legitimate_trafic/len(y_flow_pred)*100) > 80:
                self.logger.info("legitimate trafic ...")
            else:
                self.logger.info("ddos trafic ...")
                self.logger.info("victim is host: h{}".format(victim))

            self.logger.info("------------------------------------------------------------------------------")
            
            file0 = open("PredictFlowStatsfile.csv","w")
            
            file0.write('timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
            file0.close()

        except:
            pass