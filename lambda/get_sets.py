import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeDeserializer


_dynamodb = boto3.client("dynamodb")
_deserializer = TypeDeserializer()


def _deserialize_item(item):
    return {k: _deserializer.deserialize(v) for k, v in item.items()}


def _json_default(value):
    if isinstance(value, Decimal):
        # Keep integers as ints; fallback to float for non-integers
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def lambda_handler(event, context):
    table_name = os.environ.get("SETS_TABLE", "Sets")

    try:
        items = []
        scan_kwargs = {"TableName": table_name}

        while True:
            resp = _dynamodb.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        sets = [_deserialize_item(it) for it in items]

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(sets, default=_json_default),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }
