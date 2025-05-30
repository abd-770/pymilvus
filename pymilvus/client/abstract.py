import abc
from typing import Any, Dict, List, Optional, Tuple, Union

import ujson

from pymilvus.exceptions import DataTypeNotMatchException, ExceptionsMessage, MilvusException
from pymilvus.grpc_gen import common_pb2, schema_pb2
from pymilvus.settings import Config

from . import entity_helper, utils
from .constants import DEFAULT_CONSISTENCY_LEVEL, RANKER_TYPE_RRF, RANKER_TYPE_WEIGHTED
from .types import DataType, FunctionType


class FieldSchema:
    def __init__(self, raw: Any):
        self._raw = raw

        self.field_id = 0
        self.name = None
        self.is_primary = False
        self.description = None
        self.auto_id = False
        self.type = DataType.UNKNOWN
        self.indexes = []
        self.params = {}
        self.is_partition_key = False
        self.is_dynamic = False
        self.nullable = False
        self.default_value = None
        self.is_function_output = False
        # For array field
        self.element_type = None
        self.is_clustering_key = False
        self.__pack(self._raw)

    def __pack(self, raw: Any):
        self.field_id = raw.fieldID
        self.name = raw.name
        self.is_primary = raw.is_primary_key
        self.description = raw.description
        self.auto_id = raw.autoID
        self.type = DataType(raw.data_type)
        self.is_partition_key = raw.is_partition_key
        self.element_type = DataType(raw.element_type)
        self.is_clustering_key = raw.is_clustering_key
        self.default_value = raw.default_value
        if raw.default_value is not None and raw.default_value.WhichOneof("data") is None:
            self.default_value = None
        self.is_dynamic = raw.is_dynamic
        self.nullable = raw.nullable
        self.is_function_output = raw.is_function_output

        for type_param in raw.type_params:
            if type_param.key == "params":
                import json

                self.params[type_param.key] = json.loads(type_param.value)
            else:
                if type_param.key in ["mmap.enabled"]:
                    self.params["mmap_enabled"] = (
                        bool(type_param.value) if type_param.value.lower() != "false" else False
                    )
                    continue
                self.params[type_param.key] = type_param.value
                if type_param.key in ["dim"]:
                    self.params[type_param.key] = int(type_param.value)
                if type_param.key in [Config.MaxVarCharLengthKey] and raw.data_type in (
                    DataType.VARCHAR,
                    DataType.ARRAY,
                ):
                    self.params[type_param.key] = int(type_param.value)

                # TO-DO: use constants defined in orm
                if type_param.key in ["max_capacity"] and raw.data_type == DataType.ARRAY:
                    self.params[type_param.key] = int(type_param.value)

        index_dict = {}
        for index_param in raw.index_params:
            if index_param.key == "params":
                import json

                index_dict[index_param.key] = json.loads(index_param.value)
            else:
                index_dict[index_param.key] = index_param.value

        self.indexes.extend([index_dict])

    def dict(self):
        _dict = {
            "field_id": self.field_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "params": self.params or {},
        }
        if self.default_value is not None:
            # default_value is nil match this situation
            if self.default_value.WhichOneof("data") is None:
                self.default_value = None
            else:
                _dict["default_value"] = self.default_value

        if self.element_type:
            _dict["element_type"] = self.element_type

        if self.is_partition_key:
            _dict["is_partition_key"] = True
        if self.is_dynamic:
            _dict["is_dynamic"] = True
        if self.auto_id:
            _dict["auto_id"] = True
        if self.nullable:
            _dict["nullable"] = True
        if self.is_primary:
            _dict["is_primary"] = self.is_primary
        if self.is_clustering_key:
            _dict["is_clustering_key"] = True
        if self.is_function_output:
            _dict["is_function_output"] = True
        return _dict


class FunctionSchema:
    def __init__(self, raw: Any):
        self._raw = raw

        self.name = None
        self.description = None
        self.type = None
        self.params = {}
        self.input_field_names = []
        self.input_field_ids = []
        self.output_field_names = []
        self.output_field_ids = []
        self.id = 0

        self.__pack(self._raw)

    def __pack(self, raw: Any):
        self.name = raw.name
        self.description = raw.description
        self.id = raw.id
        self.type = FunctionType(raw.type)
        self.params = {}
        for param in raw.params:
            self.params[param.key] = param.value
        self.input_field_names = raw.input_field_names
        self.input_field_ids = raw.input_field_ids
        self.output_field_names = raw.output_field_names
        self.output_field_ids = raw.output_field_ids

    def dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "params": self.params,
            "input_field_names": self.input_field_names,
            "input_field_ids": self.input_field_ids,
            "output_field_names": self.output_field_names,
            "output_field_ids": self.output_field_ids,
        }


class CollectionSchema:
    def __init__(self, raw: Any):
        self._raw = raw

        self.collection_name = None
        self.description = None
        self.params = {}
        self.fields = []
        self.functions = []
        self.statistics = {}
        self.auto_id = False  # auto_id is not in collection level any more later
        self.aliases = []
        self.collection_id = 0
        self.consistency_level = DEFAULT_CONSISTENCY_LEVEL  # by default
        self.properties = {}
        self.num_shards = 0
        self.num_partitions = 0
        self.enable_dynamic_field = False
        self.created_timestamp = 0
        if self._raw:
            self.__pack(self._raw)

    def __pack(self, raw: Any):
        self.collection_name = raw.schema.name
        self.description = raw.schema.description
        self.aliases = list(raw.aliases)
        self.collection_id = raw.collectionID
        self.num_shards = raw.shards_num
        self.num_partitions = raw.num_partitions
        self.created_timestamp = raw.created_timestamp
        # keep compatible with older Milvus
        try:
            self.consistency_level = raw.consistency_level
        except Exception:
            self.consistency_level = DEFAULT_CONSISTENCY_LEVEL

        try:
            self.enable_dynamic_field = raw.schema.enable_dynamic_field
        except Exception:
            self.enable_dynamic_field = False

        # TODO: extra_params here
        # for kv in raw.extra_params:

        self.fields = [FieldSchema(f) for f in raw.schema.fields]
        self.functions = [FunctionSchema(f) for f in raw.schema.functions]
        function_output_field_names = [f for fn in self.functions for f in fn.output_field_names]
        for field in self.fields:
            if field.name in function_output_field_names:
                field.is_function_output = True
        # for s in raw.statistics:

        for p in raw.properties:
            self.properties[p.key] = p.value

    @classmethod
    def _rewrite_schema_dict(cls, schema_dict: Dict):
        fields = schema_dict.get("fields", [])
        if not fields:
            return

        for field_dict in fields:
            if field_dict.get("auto_id", None) is not None:
                schema_dict["auto_id"] = field_dict["auto_id"]
                return

    def dict(self):
        if not self._raw:
            return {}
        _dict = {
            "collection_name": self.collection_name,
            "auto_id": self.auto_id,
            "num_shards": self.num_shards,
            "description": self.description,
            "fields": [f.dict() for f in self.fields],
            "functions": [f.dict() for f in self.functions],
            "aliases": self.aliases,
            "collection_id": self.collection_id,
            "consistency_level": self.consistency_level,
            "properties": self.properties,
            "num_partitions": self.num_partitions,
            "enable_dynamic_field": self.enable_dynamic_field,
        }

        if self.created_timestamp != 0:
            _dict["created_timestamp"] = self.created_timestamp
        self._rewrite_schema_dict(_dict)
        return _dict

    def __str__(self):
        return self.dict().__str__()


class MutationResult:
    def __init__(self, raw: Any):
        self._raw = raw
        self._primary_keys = []
        self._insert_cnt = 0
        self._delete_cnt = 0
        self._upsert_cnt = 0
        self._timestamp = 0
        self._succ_index = []
        self._err_index = []
        self._cost = 0

        self._pack(raw)

    @property
    def primary_keys(self):
        return self._primary_keys

    @property
    def insert_count(self):
        return self._insert_cnt

    @property
    def delete_count(self):
        return self._delete_cnt

    @property
    def upsert_count(self):
        return self._upsert_cnt

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def succ_count(self):
        return len(self._succ_index)

    @property
    def err_count(self):
        return len(self._err_index)

    @property
    def succ_index(self):
        return self._succ_index

    @property
    def err_index(self):
        return self._err_index

    # The unit of this cost is vcu, similar to token
    @property
    def cost(self):
        return self._cost

    def __str__(self):
        if self.cost:
            return (
                f"(insert count: {self._insert_cnt}, delete count: {self._delete_cnt}, upsert count: {self._upsert_cnt}, "
                f"timestamp: {self._timestamp}, success count: {self.succ_count}, err count: {self.err_count}, "
                f"cost: {self._cost})"
            )
        return (
            f"(insert count: {self._insert_cnt}, delete count: {self._delete_cnt}, upsert count: {self._upsert_cnt}, "
            f"timestamp: {self._timestamp}, success count: {self.succ_count}, err count: {self.err_count}"
        )

    __repr__ = __str__

    # TODO
    # def error_code(self):
    #     pass
    #
    # def error_reason(self):
    #     pass

    def _pack(self, raw: Any):
        which = raw.IDs.WhichOneof("id_field")
        if which == "int_id":
            self._primary_keys = raw.IDs.int_id.data
        elif which == "str_id":
            self._primary_keys = raw.IDs.str_id.data

        self._insert_cnt = raw.insert_cnt
        self._delete_cnt = raw.delete_cnt
        self._upsert_cnt = raw.upsert_cnt
        self._timestamp = raw.timestamp
        self._succ_index = raw.succ_index
        self._err_index = raw.err_index
        self._cost = int(
            raw.status.extra_info["report_value"] if raw.status and raw.status.extra_info else "0"
        )


class BaseRanker:
    def __int__(self):
        return

    def dict(self):
        return {}

    def __str__(self):
        return self.dict().__str__()


class RRFRanker(BaseRanker):
    def __init__(
        self,
        k: int = 60,
    ):
        self._strategy = RANKER_TYPE_RRF
        self._k = k

    def dict(self):
        params = {
            "k": self._k,
        }
        return {
            "strategy": self._strategy,
            "params": params,
        }


class WeightedRanker(BaseRanker):
    def __init__(self, *nums, norm_score: bool = True):
        self._strategy = RANKER_TYPE_WEIGHTED
        weights = []
        for num in nums:
            # isinstance(True, int) is True, thus we need to check bool first
            if isinstance(num, bool) or not isinstance(num, (int, float)):
                error_msg = f"Weight must be a number, got {type(num)}"
                raise TypeError(error_msg)
            weights.append(num)
        self._weights = weights
        self._norm_score = norm_score

    def dict(self):
        params = {
            "weights": self._weights,
            "norm_score": self._norm_score,
        }
        return {
            "strategy": self._strategy,
            "params": params,
        }


class AnnSearchRequest:
    def __init__(
        self,
        data: Union[List, utils.SparseMatrixInputType],
        anns_field: str,
        param: Dict,
        limit: int,
        expr: Optional[str] = None,
        expr_params: Optional[dict] = None,
    ):
        self._data = data
        self._anns_field = anns_field
        self._param = param
        self._limit = limit

        if expr is not None and not isinstance(expr, str):
            raise DataTypeNotMatchException(message=ExceptionsMessage.ExprType % type(expr))
        self._expr = expr
        self._expr_params = expr_params

    @property
    def data(self):
        return self._data

    @property
    def anns_field(self):
        return self._anns_field

    @property
    def param(self):
        return self._param

    @property
    def limit(self):
        return self._limit

    @property
    def expr(self):
        return self._expr

    @property
    def expr_params(self):
        return self._expr_params

    def __str__(self):
        return {
            "anns_field": self.anns_field,
            "param": self.param,
            "limit": self.limit,
            "expr": self.expr,
        }.__str__()


class SearchResult(list):
    """nq results: List[Hits]"""

    def __init__(
        self,
        res: schema_pb2.SearchResultData,
        round_decimal: Optional[int] = None,
        status: Optional[common_pb2.Status] = None,
        session_ts: Optional[int] = 0,
    ):
        self._nq = res.num_queries
        all_topks = res.topks
        self.recalls = res.recalls
        self._pk_name = res.primary_field_name or "id"

        self.cost = int(status.extra_info["report_value"] if status and status.extra_info else "0")

        output_fields = res.output_fields
        fields_data = res.fields_data

        all_pks: List[Union[str, int]] = []
        all_scores: List[float] = []

        if res.ids.HasField("int_id"):
            all_pks = res.ids.int_id.data
        elif res.ids.HasField("str_id"):
            all_pks = res.ids.str_id.data

        if isinstance(round_decimal, int) and round_decimal > 0:
            all_scores = [round(x, round_decimal) for x in res.scores]
        else:
            all_scores = res.scores

        data = []
        nq_thres = 0
        for topk in all_topks:
            start, end = nq_thres, nq_thres + topk
            nq_th_fields = self.get_fields_by_range(start, end, fields_data)
            data.append(
                Hits(
                    topk,
                    all_pks[start:end],
                    all_scores[start:end],
                    nq_th_fields,
                    output_fields,
                    self._pk_name,
                )
            )
            nq_thres += topk
        self._session_ts = session_ts
        self._search_iterator_v2_results = res.search_iterator_v2_results
        super().__init__(data)

    def get_session_ts(self):
        return self._session_ts

    def get_search_iterator_v2_results_info(self):
        return self._search_iterator_v2_results

    def get_fields_by_range(
        self, start: int, end: int, all_fields_data: List[schema_pb2.FieldData]
    ) -> Dict[str, Tuple[List[Any], schema_pb2.FieldData]]:
        field2data: Dict[str, Tuple[List[Any], schema_pb2.FieldData]] = {}

        for field in all_fields_data:
            name, scalars, dtype = field.field_name, field.scalars, field.type
            field_meta = schema_pb2.FieldData(
                type=dtype,
                field_name=name,
                field_id=field.field_id,
                is_dynamic=field.is_dynamic,
            )
            if dtype == DataType.BOOL:
                field2data[name] = (
                    apply_valid_data(
                        scalars.bool_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype in (DataType.INT8, DataType.INT16, DataType.INT32):
                field2data[name] = (
                    apply_valid_data(
                        scalars.int_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype == DataType.INT64:
                field2data[name] = (
                    apply_valid_data(
                        scalars.long_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype == DataType.FLOAT:
                field2data[name] = (
                    apply_valid_data(
                        scalars.float_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype == DataType.DOUBLE:
                field2data[name] = (
                    apply_valid_data(
                        scalars.double_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype == DataType.VARCHAR:
                field2data[name] = (
                    apply_valid_data(
                        scalars.string_data.data[start:end], field.valid_data, start, end
                    ),
                    field_meta,
                )
                continue

            if dtype == DataType.JSON:
                res = apply_valid_data(
                    scalars.json_data.data[start:end], field.valid_data, start, end
                )
                json_dict_list = [ujson.loads(item) if item is not None else item for item in res]
                field2data[name] = json_dict_list, field_meta
                continue

            if dtype == DataType.ARRAY:
                res = apply_valid_data(
                    scalars.array_data.data[start:end], field.valid_data, start, end
                )
                field2data[name] = (
                    extract_array_row_data(res, scalars.array_data.element_type),
                    field_meta,
                )
                continue

            # vectors
            dim, vectors = field.vectors.dim, field.vectors
            field_meta.vectors.dim = dim
            if dtype == DataType.FLOAT_VECTOR:
                if start == 0 and (end - start) * dim >= len(vectors.float_vector.data):
                    # If the range equals to the length of vectors.float_vector.data, direct return
                    # it to avoid a copy. This logic improves performance by 25% for the case
                    # retrival 1536 dim embeddings with topk=16384.
                    field2data[name] = vectors.float_vector.data, field_meta
                else:
                    field2data[name] = (
                        vectors.float_vector.data[start * dim : end * dim],
                        field_meta,
                    )
                continue

            if dtype == DataType.BINARY_VECTOR:
                field2data[name] = (
                    vectors.binary_vector[start * (dim // 8) : end * (dim // 8)],
                    field_meta,
                )
                continue
            # TODO(SPARSE): do we want to allow the user to specify the return format?
            if dtype == DataType.SPARSE_FLOAT_VECTOR:
                field2data[name] = (
                    entity_helper.sparse_proto_to_rows(vectors.sparse_float_vector, start, end),
                    field_meta,
                )
                continue

            if dtype == DataType.BFLOAT16_VECTOR:
                field2data[name] = (
                    vectors.bfloat16_vector[start * (dim * 2) : end * (dim * 2)],
                    field_meta,
                )
                continue

            if dtype == DataType.FLOAT16_VECTOR:
                field2data[name] = (
                    vectors.float16_vector[start * (dim * 2) : end * (dim * 2)],
                    field_meta,
                )
                continue

            if dtype == DataType.INT8_VECTOR:
                field2data[name] = (
                    vectors.int8_vector[start * dim : end * dim],
                    field_meta,
                )
                continue
        return field2data

    def __str__(self) -> str:
        """Only print at most 10 query results"""
        reminder = f" ... and {len(self) - 10} results remaining" if len(self) > 10 else ""
        recall_msg = (
            f", recalls: {list(map(str, self.recalls[:10]))}" if len(self.recalls) > 0 else ""
        ) + (
            f" ... and {len(self.recalls) - 10} recall results remaining"
            if len(self.recalls) > 10
            else ""
        )
        cost_msg = f", cost: {self.cost}" if self.cost else ""
        return f"data: {list(map(str, self[:10]))}{reminder}{recall_msg}{cost_msg}"

    __repr__ = __str__


class Hits(list):
    ids: List[Union[str, int]]
    distances: List[float]

    def __init__(
        self,
        topk: int,
        pks: List[Union[int, str]],
        distances: List[float],
        fields: Dict[str, Tuple[List[Any], schema_pb2.FieldData]],
        output_fields: List[str],
        pk_name: str,
    ):
        """
        Args:
            fields(Dict[str, Tuple[List[Any], schema_pb2.FieldData]]):
                field name to a tuple of topk data and field meta
        """
        self.ids = pks
        self.distances = distances
        self._pk_name = pk_name

        all_fields = list(fields.keys())
        dynamic_fields = list(set(output_fields) - set(all_fields))

        hits = []
        for i in range(topk):
            curr_field = {}
            for fname, (data, field_meta) in fields.items():
                if len(data) <= i:
                    curr_field[fname] = None
                # Get dense vectors
                if field_meta.type in (
                    DataType.FLOAT_VECTOR,
                    DataType.BINARY_VECTOR,
                    DataType.BFLOAT16_VECTOR,
                    DataType.FLOAT16_VECTOR,
                    DataType.INT8_VECTOR,
                ):
                    dim = field_meta.vectors.dim
                    if field_meta.type in [DataType.BINARY_VECTOR]:
                        dim = dim // 8
                    elif field_meta.type in [DataType.BFLOAT16_VECTOR, DataType.FLOAT16_VECTOR]:
                        dim = dim * 2
                    curr_field[fname] = data[i * dim : (i + 1) * dim]
                    continue

                # Get dynamic fields
                if field_meta.type == DataType.JSON and field_meta.is_dynamic:
                    if len(dynamic_fields) > 0:
                        curr_field.update({k: v for k, v in data[i].items() if k in dynamic_fields})
                        continue

                    if fname in output_fields:
                        curr_field.update(data[i])
                        continue

                # sparse float vector and other fields
                curr_field[fname] = data[i]

            hits.append(Hit(pks[i], distances[i], curr_field, self._pk_name))

        super().__init__(hits)

    def __str__(self) -> str:
        """Only print at most 10 query results"""
        reminder = f" ... and {len(self) - 10} entities remaining" if len(self) > 10 else ""
        return f"{list(map(str, self[:10]))!s}{reminder}"

    __repr__ = __str__


class Hit:
    id: Union[int, str]
    distance: float
    fields: Dict[str, Any]

    def __init__(self, pk: Union[int, str], distance: float, fields: Dict[str, Any], pk_name: str):
        self.id = pk
        self.distance = distance
        self.fields = fields
        self._pk_name = pk_name

    def __getattr__(self, item: str):
        if item not in self.fields:
            raise MilvusException(message=f"Field {item} is not in the hit entity")
        return self.fields[item]

    @property
    def entity(self):
        return self

    @property
    def pk(self) -> Union[str, int]:
        return self.id

    @property
    def score(self) -> float:
        return self.distance

    def get(self, field_name: str) -> Any:
        return self.fields.get(field_name)

    def __str__(self) -> str:
        return f"{self._pk_name}: {self.id}, distance: {self.distance}, entity: {self.fields}"

    __repr__ = __str__

    def to_dict(self):
        return {
            self._pk_name: self.id,
            "distance": self.distance,
            "entity": self.fields,
        }


def extract_array_row_data(
    scalars: List[schema_pb2.ScalarField], element_type: DataType
) -> List[List[Any]]:
    row = []
    for ith_array in scalars:
        if ith_array is None:
            row.append(None)
            continue

        if element_type == DataType.INT64:
            row.append(ith_array.long_data.data)
            continue

        if element_type == DataType.BOOL:
            row.append(ith_array.bool_data.data)
            continue

        if element_type in (DataType.INT8, DataType.INT16, DataType.INT32):
            row.append(ith_array.int_data.data)
            continue

        if element_type == DataType.FLOAT:
            row.append(ith_array.float_data.data)
            continue

        if element_type == DataType.DOUBLE:
            row.append(ith_array.double_data.data)
            continue

        if element_type in (DataType.STRING, DataType.VARCHAR):
            row.append(ith_array.string_data.data)
            continue
    return row


def apply_valid_data(
    data: List[Any], valid_data: Union[None, List[bool]], start: int, end: int
) -> List[Any]:
    if valid_data:
        for i, valid in enumerate(valid_data[start:end]):
            if not valid:
                data[i] = None
    return data


class LoopBase:
    def __init__(self):
        self.__index = 0

    def __iter__(self):
        return self

    def __getitem__(self, item: Any):
        if isinstance(item, slice):
            _start = item.start or 0
            _end = min(item.stop, self.__len__()) if item.stop else self.__len__()
            _step = item.step or 1

            return [self.get__item(i) for i in range(_start, _end, _step)]

        if item >= self.__len__():
            msg = "Index out of range"
            raise IndexError(msg)

        return self.get__item(item)

    def __next__(self):
        while self.__index < self.__len__():
            self.__index += 1
            return self.__getitem__(self.__index - 1)

        # iterate stop, raise Exception
        self.__index = 0
        raise StopIteration

    def __str__(self):
        return str(list(map(str, self.__getitem__(slice(0, 10)))))

    @abc.abstractmethod
    def get__item(self, item: Any):
        raise NotImplementedError
