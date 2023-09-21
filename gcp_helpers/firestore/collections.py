import json
import os
from dataclasses import field, dataclass
from typing import Generator, Any

from google.cloud import firestore
from google.oauth2 import service_account


def get_firestore_client(project, db=None) -> firestore.Client:
    key = os.environ.get("SECRET_ACCOUNT_KEY", None)
    if key is None:
        client = firestore.Client(project=project, database=db)
    else:
        client = firestore.Client(project=project, database=db,
                                  credentials=service_account.Credentials.from_service_account_file(key))
    return client


class FirestoreResult:
    def __init__(self, document: firestore.DocumentSnapshot):
        self.doc = document

    def dict(self, append_id=True):
        doc = self.doc.to_dict()
        if append_id:
            doc.update({"docId": self.doc.id})
        return doc

    def to_class(self, class_ref: type):
        try:
            return class_ref(**self.dict())
        except TypeError as e:
            print(f"TypeError: {e}")
            # Handle the exception or return an alternative value if desired
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            # Handle the exception or return an alternative value if desired
            return None


class FirestoreMultiResult:
    def __init__(self, stream: Generator[firestore.DocumentSnapshot, Any, None]):
        self._stream = stream
        self.raw: list[firestore.DocumentSnapshot] = []

        self._to_raw()

    def _to_raw(self):
        self.raw = [doc for doc in self._stream]

    def to_list(self, append_id=True, class_ref: type = None) -> list[any]:
        res = []
        for doc in self.raw:
            item = doc.to_dict()
            if append_id:
                item["docId"] = doc.id
            if class_ref and isinstance(class_ref, type):
                res.append(class_ref(**item))
            else:
                res.append(item)
        return res

    def to_dict(self, append_id=False, class_ref: type = None) -> dict[str, any]:
        res = {}
        for doc in self.raw:
            docId = doc.id
            item = {
                f"{docId}": doc.to_dict()
            }
            if append_id:
                item[docId]["docId"] = doc.id
            res.update(item)
        return res

    def len(self):
        return len(self.raw)


@dataclass
class FirestoreOrderBy:
    field_path: str
    direction: str = field(default=firestore.Query.ASCENDING)

    def ASC(self):
        self.direction = firestore.Query.ASCENDING

    def DESC(self):
        self.direction = firestore.Query.DESCENDING


class FirestoreFilter:

    @classmethod
    def custom(cls, field_name: str, operator: str, value: Any):
        return firestore.FieldFilter(field_name, operator, value)

    @classmethod
    def equal(cls, field_name: str, value: Any):
        return firestore.FieldFilter(field_name, "==", value)

    @classmethod
    def not_equal(cls, field_name: str, value: Any):
        return firestore.FieldFilter(field_name, "!=", value)

    @classmethod
    def value_in(cls, field_name: str, value_list: list[Any]):
        return firestore.FieldFilter(field_name, "in", value_list)

    @classmethod
    def value_not_in(cls, field_name: str, value_list: list[Any]):
        return firestore.FieldFilter(field_name, "not-in", value_list)

    @classmethod
    def array_field_contains(cls, array_field_name: str, value):
        return firestore.FieldFilter(array_field_name, "array-contains", value)

    @classmethod
    def array_field_contains_any(cls, array_field_name: str, value):
        return firestore.FieldFilter(array_field_name, "array-contains-any", value)


class FirestoreCollection:
    def __init__(self, project, db_name, collection_name):
        self._cli = get_firestore_client(project=project, db=db_name)
        self._col_ref = self._cli.collection(collection_name)

    def get_all(self):
        stream = self._col_ref.stream()

        return FirestoreMultiResult(stream)

    def search(self, field_filter: firestore.FieldFilter | list[firestore.FieldFilter] = None,
               order_by: FirestoreOrderBy | None = None, limit: int | None = None):
        query = self._col_ref
        if field_filter and isinstance(field_filter, firestore.FieldFilter):
            query = self._col_ref.where(filter=field_filter)
        elif field_filter and isinstance(field_filter, list):
            for f in field_filter:
                query = query.where(filter=f)
        if order_by:
            query = query.order_by(order_by.field_path, direction=order_by.direction)
        if limit:
            query = query.limit(limit)

        stream = query.stream()
        return FirestoreMultiResult(stream)

    def get_one(self, docId):
        doc_ref = self._col_ref.document(docId)
        doc = doc_ref.get()
        if doc and doc.exists:
            return FirestoreResult(doc)
        else:
            return None

    def is_document_exists(self, docId):
        doc = self.get_one(docId)
        return True if doc else False

    def update(self, docId, field_updates):
        # print('id -> {} |\ndata ->{}'.format(id, data))
        doc_ref = self._col_ref.document(docId)
        res = doc_ref.update(field_updates)
        # print(res)
        return res

    def add(self, fields: dict, docId: str | None = None):
        res = self._col_ref.add(fields, docId)
        return res

    def delete_by_path(self, document_path):
        res = self._cli.document(document_path).delete()
        return res

    def delete(self, docId):
        res = self._col_ref.document(docId).delete()
        return res


class FirestoreCollectionGroup:
    def __init__(self, project, db_name, collection_group_name):
        self._cli = get_firestore_client(project=project, db=db_name)
        self._collection_group_name = collection_group_name
        self._col_ref = self._cli.collection_group(collection_group_name)

    def delete(self, docId, parent_path):
        doc_path = f"{parent_path}/{docId}"
        return self._cli.document(doc_path).delete()

    def add(self, docId, parent_path, fields):
        res = self._cli.collection(parent_path).add(fields, docId)
        return res

    def update(self, docId, parent_path, field_updates):
        doc_path = f"{parent_path}/{docId}"
        doc_ref = self._cli.document(doc_path)
        res = doc_ref.update(field_updates)
        return res

    def get_all(self):
        stream = self._col_ref.stream()
        return FirestoreMultiResult(stream)

    def get_one(self, docId, parent_path):
        doc_path = f"{parent_path}/{docId}"
        doc_ref = self._cli.document(doc_path)
        document = doc_ref.get()
        if document and document.exists:
            return FirestoreResult(document)
        else:
            return None

    def get_first_from_stream(self, docId):
        query = self._col_ref.limit(1).stream()
        document = next((doc for doc in query if doc.id == docId), None)
        if document and document.exists:
            return FirestoreResult(document)
        else:
            return None

    def search(self, field_filter: firestore.FieldFilter | list[firestore.FieldFilter] = None,
               order_by: FirestoreOrderBy | None = None, limit: int | None = None):
        query = self._col_ref
        if field_filter and isinstance(field_filter, list):
            for f in field_filter:
                query = query.where(filter=f)
        elif field_filter and isinstance(field_filter, firestore.FieldFilter):
            query = self._col_ref.where(filter=field_filter)
        if order_by:
            query = query.order_by(order_by.field_path, direction=order_by.direction)
        if limit:
            query = query.limit(limit)

        stream = query.stream()
        return FirestoreMultiResult(stream)
