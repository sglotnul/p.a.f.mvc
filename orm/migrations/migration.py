import json
from typing import List
from mymvc2.orm.migrations.operations.base import Operation
from mymvc2.orm.migrations import operations

#Преставляет собой одну миграцию. Содержит информацию обо все примененных в ней операциях
OPERATION_CLS = {
	"CREATE_TABLE": operations.CreateTableOperation,
	"DELETE_TABLE": operations.DeleteTableOperation,
	"CHANGE_TABLE": operations.AlterTableOperation,
}

class Migration:
	def __init__(self):
		self._operations = {}
		
	def from_entry(self, entry: dict):
		for operation_type, inner in entry.items():
			operation_cls = OPERATION_CLS.get(operation_type, None)
			assert operation_cls, "invalid operation type"
			
			for operation_definition in inner:
				table = operation_definition.pop("table")
				self._add_operation(operation_type, operation_cls(table, operation_definition))
	
	def _get_same_operations_list(self, operation_type: str) -> List[Operation]:
		same_operations_list = self._operations.get(operation_type)
		if same_operations_list is None:
			same_operations_list = []
			self._operations[operation_type] = same_operations_list
		return same_operations_list

	def _add_operation(self, operation_type: str, operation: Operation) -> Operation:
		same_operations_list = self._get_same_operations_list(operation_type)
		same_operations_list.append(operation)
		return operation

	def _execute(self, executor, query: str):
		executor(query, script=True)

	def add_create_table_operation(self, table: str, meta: dict) -> Operation:
		operation_cls = OPERATION_CLS['CREATE_TABLE']
		return self._add_operation("CREATE_TABLE", operation_cls(table, meta))

	def add_delete_table_operation(self, table: str) -> Operation:
		operation_cls = OPERATION_CLS['DELETE_TABLE']
		return self._add_operation("DELETE_TABLE", operation_cls(table))

	def add_change_table_operation(self, table: str, meta: dict) -> Operation:
		operation_cls = OPERATION_CLS['CHANGE_TABLE']
		return self._add_operation("CHANGE_TABLE", operation_cls(table, meta))

	def to_json(self) -> str:
		deconstructed_migration = {}
		for operation_type, operations in self._operations.items():
			deconstructed_migration[operation_type] = list(map(lambda o: o.deconstruct(), operations))
		return json.dumps(deconstructed_migration)

	def apply(self, executor: object):
		schema = executor.schema_engine()
		for operation_list in self._operations.values():
			for operation in operation_list:
				operation.apply(schema)
		self._execute(executor, schema.to_str())

	def apply_to_state(self, state: object):
		for operation_list in self._operations.values():
			for operation in operation_list:
				operation.apply_to_state(state)

	def __bool__(self) -> bool:
		return bool(self._operations)