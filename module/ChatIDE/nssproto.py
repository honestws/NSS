from io import BytesIO
import numpy as np
import nss_pb2

# Construct data packet


def construct_proto(username: str, msgtype: str, msg: str, para: np.ndarray, lr: np.ndarray) -> nss_pb2.NSSProtocol:
    para_bytes = BytesIO()
    lr_bytes = BytesIO()
    np.save(para_bytes, para, allow_pickle=False)
    np.save(lr_bytes, lr, allow_pickle=False)
    return nss_pb2.NSSProtocol(
        username=username, msgtype=msgtype, msg=msg, para=para_bytes.getvalue(), lr=lr_bytes.getvalue())


# Parse data packet
def parse_proto(proto: nss_pb2.NSSProtocol) -> (str, str, str, np.ndarray, np.ndarray):
    parse = nss_pb2.NSSProtocol()
    parse.ParseFromString(proto)
    username = parse.username
    msgtype = parse.msgtype
    msg = parse.msg
    para_bytes = BytesIO(parse.para)
    lr_bytes = BytesIO(parse.lr)
    return username, msgtype, msg, np.load(para_bytes, allow_pickle=False), np.load(lr_bytes, allow_pickle=False)


# Construct data packet
def res(username: str, msgtype: str, msg: str, para: np.ndarray, lr: np.ndarray) -> nss_pb2.NSSProtocol:
    para_bytes = BytesIO()
    lr_bytes = BytesIO()
    np.save(para_bytes, para, allow_pickle=False)
    np.save(lr_bytes, lr, allow_pickle=False)
    return nss_pb2.NSSProtocol(
        username=username, msgtype=msgtype, msg=msg, para=para_bytes.getvalue(), lr=lr_bytes.getvalue())


# Parse data packet
def req(proto: nss_pb2.NSSProtocol) -> (str, str, str, np.ndarray, np.ndarray):
    parse = nss_pb2.NSSProtocol()
    parse.ParseFromString(proto)
    username = parse.username
    msgtype = parse.msgtype
    msg = parse.msg
    para_bytes = BytesIO(parse.para)
    lr_bytes = BytesIO(parse.lr)
    return username, msgtype, msg, np.load(para_bytes, allow_pickle=False), np.load(lr_bytes, allow_pickle=False)
