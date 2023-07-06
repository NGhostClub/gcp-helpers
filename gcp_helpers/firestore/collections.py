import json
import os
from dataclasses import field, dataclass
from typing import Generator, Any

from google.cloud import firestore
from google.oauth2 import service_account


def get_firestore_client(project) -> firestore.Client:
    key = os.environ.get("SECRET_ACCOUNT_KEY", None)
    if key is None:
        client = firestore.Client(project=project)
    else:
        client = firestore.Client(project=project,
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
                item.update({"docId": doc.id})
            if class_ref and isinstance(class_ref, type):
                res.append(class_ref(**item))
            else:
                res.append(item)
        return res

    def to_dict(self, append_id=False, class_ref: type = None) -> dict[str, any]:
        res = {}
        for doc in self.raw:
            item = {
                doc.id: {
                    doc.to_dict()
                }
            }
            if append_id:
                item[doc.id]["docId"] = doc.id
            res.update(item)
        return res


@dataclass
class FirestoreOrderBy:
    field_path: str
    direction: str = field(default=firestore.Query.ASCENDING)

    def ASC(self):
        self.direction = firestore.Query.ASCENDING

    def DESC(self):
        self.direction = firestore.Query.DESCENDING


class FirestoreFilter(list):
    ALLOWED_OP = [
        "<",
        "<=",
        "==",
        ">",
        ">=",
        "!=",
        "array-contains"
        "array-contains",
        "in",
        "not-in"
    ]

    def __init__(self, field, op, value):
        if op not in self.ALLOWED_OP:
            raise ValueError(f"op must be one of {self.ALLOWED_OP}")
        super().__init__([field, op, value])


class FirestoreCollection:
    def __init__(self, project, collection_name):
        self._cli = get_firestore_client(project=project)
        self._col_ref = self._cli.collection(collection_name)

    def get_all(self):
        stream = self._col_ref.stream()

        return FirestoreMultiResult(stream)

    def search(self, filter_query: FirestoreFilter | list[FirestoreFilter],
               order_by: FirestoreOrderBy | None = None, limit: int | None = None):
        query = self._col_ref
        if isinstance(filter_query, list):
            for f in filter_query:
                query = query.where(*f)
        else:
            query = self._col_ref.where(*filter_query)
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


class FirestoreCollectionGroup:
    def __init__(self, project, collection_group_name):
        self._cli = get_firestore_client(project=project)
        self._collection_group_name = collection_group_name
        self._col_ref = self._cli.collection_group(collection_group_name)

    def update(self, docId, parent_path, field_updates):
        doc_path = f"{parent_path}/{docId}"
        doc_ref = self._cli.document(doc_path)
        res = doc_ref.update(field_updates)
        return res

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
