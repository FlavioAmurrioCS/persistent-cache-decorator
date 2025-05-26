# Python Rules

- Where possible, prefer duck-typing tests than `isinstance`, e.g. `hasattr(x, attr)` not `isinstance(x, SpecificClass)`
- Use modern Python 3.9+ syntax
- Prefer f-strings for formatting strings rather than `.format` or `%` formatting
- When creating log statements, never use runtime string formatting. Use the `extra` argument and % placeholders in the log message
- When generating union types, use the union operator, `|` , not the `typing.Union` type
- When merging dictionaries, use the union operator
- When writing type hints for standard generics like `dict`, `list`, `tuple`, use the PEP-585 spec, not `typing.Dict`, `typing.List`, etc.
- Use type annotations in function and method signatures, unless the rest of the code base does not have type signatures
- Do not add inline type annotations for local variables when they are declared and assigned in the same statement.
- Prefer `pathlib` over `os.path` for operations like path joining
- When using `open()` in text-mode, explicitly set `encoding` to `utf-8`
- Prefer `argparse` over `optparse`
- Use the builtin methods in the `itertools` module for common tasks on iterables rather than creating code to achieve the same result
- When creating dummy data, don't use "Foo" and "Bar", be more creative
- When creating dummy data in strings like names don't just create English data, create data in a range of languages like English, Spanish, Mandarin, and Hindi
- When asked to create a function, class, or other piece of standalone code, don't append example calls unless otherwise told to
