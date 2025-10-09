from thaumic.base.sqlfield import SQLField


class MsSQLField(SQLField):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@staticmethod
	def derive_type_from_decl(declstr):
		raise NotImplementedError


