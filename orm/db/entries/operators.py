from mymvc2.orm.db.operator import Operator

class InsertIntoOperator(Operator):
	CMD = "INSERT INTO {}"

	def __init__(self):
		self._table = None

	def set(self, table: str):
		self._table = table

	def __str__(self) -> str:
		return self.CMD.format(self._table)

	def __bool__(self) -> bool:
		return bool(self._table)

class InsertValuesOperator(Operator):
	CMD = "({fields}) VALUES ({values})"
	VALUE = "\"{}\""

	def __init__(self):
		self._values = {}

	def set(self, field: str, value: any):
		self._values[field] = value

	def __str__(self) -> str:
		separator = ","
		return self.CMD.format(
			fields=separator.join(self._values.keys()), 
			values=separator.join(map(lambda val: self.VALUE.format(val) if not isinstance(val, int) else val, self._values.values()))
		)

	def __bool__(self) -> bool:
		return bool(self._values)

class DeleteFromOperator(InsertIntoOperator):
	CMD = "DELETE FROM {}"