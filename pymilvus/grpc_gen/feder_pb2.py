# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: feder.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'feder.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import common_pb2 as common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x66\x65\x64\x65r.proto\x12\x12milvus.proto.feder\x1a\x0c\x63ommon.proto\"9\n\x10SegmentIndexData\x12\x11\n\tsegmentID\x18\x01 \x01(\x03\x12\x12\n\nindex_data\x18\x02 \x01(\t\"A\n\x18\x46\x65\x64\x65rSegmentSearchResult\x12\x11\n\tsegmentID\x18\x01 \x01(\x03\x12\x12\n\nvisit_info\x18\x02 \x01(\t\"t\n\x19ListIndexedSegmentRequest\x12*\n\x04\x62\x61se\x18\x01 \x01(\x0b\x32\x1c.milvus.proto.common.MsgBase\x12\x17\n\x0f\x63ollection_name\x18\x02 \x01(\t\x12\x12\n\nindex_name\x18\x03 \x01(\t\"]\n\x1aListIndexedSegmentResponse\x12+\n\x06status\x18\x01 \x01(\x0b\x32\x1b.milvus.proto.common.Status\x12\x12\n\nsegmentIDs\x18\x02 \x03(\x03\"\x8f\x01\n\x1f\x44\x65scribeSegmentIndexDataRequest\x12*\n\x04\x62\x61se\x18\x01 \x01(\x0b\x32\x1c.milvus.proto.common.MsgBase\x12\x17\n\x0f\x63ollection_name\x18\x02 \x01(\t\x12\x12\n\nindex_name\x18\x03 \x01(\t\x12\x13\n\x0bsegmentsIDs\x18\x04 \x03(\x03\"\xb9\x02\n DescribeSegmentIndexDataResponse\x12+\n\x06status\x18\x01 \x01(\x0b\x32\x1b.milvus.proto.common.Status\x12W\n\nindex_data\x18\x02 \x03(\x0b\x32\x43.milvus.proto.feder.DescribeSegmentIndexDataResponse.IndexDataEntry\x12\x37\n\x0cindex_params\x18\x03 \x03(\x0b\x32!.milvus.proto.common.KeyValuePair\x1aV\n\x0eIndexDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\x03\x12\x33\n\x05value\x18\x02 \x01(\x0b\x32$.milvus.proto.feder.SegmentIndexData:\x02\x38\x01\x42\x35Z3github.com/milvus-io/milvus-proto/go-api/v2/federpbb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'feder_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z3github.com/milvus-io/milvus-proto/go-api/v2/federpb'
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE_INDEXDATAENTRY']._loaded_options = None
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE_INDEXDATAENTRY']._serialized_options = b'8\001'
  _globals['_SEGMENTINDEXDATA']._serialized_start=49
  _globals['_SEGMENTINDEXDATA']._serialized_end=106
  _globals['_FEDERSEGMENTSEARCHRESULT']._serialized_start=108
  _globals['_FEDERSEGMENTSEARCHRESULT']._serialized_end=173
  _globals['_LISTINDEXEDSEGMENTREQUEST']._serialized_start=175
  _globals['_LISTINDEXEDSEGMENTREQUEST']._serialized_end=291
  _globals['_LISTINDEXEDSEGMENTRESPONSE']._serialized_start=293
  _globals['_LISTINDEXEDSEGMENTRESPONSE']._serialized_end=386
  _globals['_DESCRIBESEGMENTINDEXDATAREQUEST']._serialized_start=389
  _globals['_DESCRIBESEGMENTINDEXDATAREQUEST']._serialized_end=532
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE']._serialized_start=535
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE']._serialized_end=848
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE_INDEXDATAENTRY']._serialized_start=762
  _globals['_DESCRIBESEGMENTINDEXDATARESPONSE_INDEXDATAENTRY']._serialized_end=848
# @@protoc_insertion_point(module_scope)
