from pafmvc.orm.db.connection import connect
from pafmvc.orm.model.query_set import QuerySet

class Manager:
	def __init__(self, model_cls: type):
		self._model = model_cls

		self._executor = connect()
		self._data_engine = self._executor.data_engine()
	
	def _execute(self, query: str) -> iter:
		self._executor.connect()
		return self._executor(query)

	def get_queryset(self):
		return QuerySet(self._model, self._executor)

	def all(self) -> QuerySet:
		return self.get_queryset()

	def filter(self, **params) -> QuerySet:
		return self.get_queryset().filter(**params)

	def get(self, **params) -> object:
		model = self.get_queryset().get(**params)
		return model

	def _create_entry(self, query: str) -> int:
		cur = self._execute(query)
		last_id = cur.lastrowid
		self._executor.close()
		return last_id
	
	def create(self, **cols):
		inserter = self._data_engine.insert(self._model.meta.name)
		for field in self._model.meta.fields:
			if not field.autoincrement:
				val = cols.get(field.name, None)
				if val is None:
					raise Exception(f"{field.name} field is reqired")
				inserter.insert(field.name, val)	
		lastrowid = self._create_entry(inserter.to_str())
		return self.get(id=lastrowid)

	def remove(self, **params):
		self._execute(self._data_engine.remove(self._model.meta.name).where(**params).to_str())
		self._executor.close()

	def update(self, cols: dict, **params):
		updater = self._data_engine.update(self._model.meta.name).where(**params)
		for col, val in cols.items():
			updater.set(col, val)
		self._execute(updater.to_str())
		self._executor.close()