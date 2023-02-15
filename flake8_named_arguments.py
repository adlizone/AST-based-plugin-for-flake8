import ast
import sys
import importlib
from typing import Any
from typing import Generator
from typing import Tuple
from typing import List
from typing import Type

if sys.version_info < (3, 8):
    import importlib.metadata
else:
    import importlib.metadata as importlib_metadata

MSG = 'FNA100 all arguments in ** are identifiers'
MSG_2 = 'FNA101 useless ternary operator'

class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.problems: List[Tuple[int, int]] = []
    
    def visit_Call(self, node: ast.Call) -> None:
        for keyword in node.keywords:
            if (
                    keyword.arg is None and
                    isinstance(keyword.value, ast.Dict) and
                    all(
                        isinstance(key, ast.Str)
                        for key in keyword.value.keys
                        ) and
                        all(
                            key.s.isidentifier()
                            for key in keyword.value.keys
                            )
                ):
                    self.problems.append({node.lineno,node.col_offset})
            
        self.generic_visit(node)

        
class Visitor_second(ast.NodeVisitor):
    def __init__(self) -> None:
        self.useless_ternary_operator: List[tuple[int,int]] = []

    def visit_IfExp(self, node: ast.IfExp) -> None:
        
        self._check_number_of_objects(node)
        self._check_same_return_values(node)
        self._check_return_value_none(node)

        self.generic_visit(node)

    def _check_number_of_objects(self, node: ast.IfExp):
        if (
                isinstance(node.test, ast.Compare)
                and len(node.test.ops) == 1
                and (
                        isinstance(node.test.ops[0], ast.Eq)
                        or isinstance(node.test.ops[0], ast.NotEq)
                    )
            ):
            ids = set()

            if isinstance(node.body, ast.Name):
                ids.add(node.body.id)
            if isinstance(node.orelse, ast.Name):
                ids.add(node.orelse.id)

            if isinstance(node.test.left, ast.Name):
                ids.add(node.test.left.id)
            if (
                    len(node.test.comparators) == 1
                    and isinstance(node.test.comparators[0],ast.Name)
                ):
                ids.add(node.test.comparators[0].id)

                if len(ids) < 3:
                    self.useless_ternary_operator.append({node.lineno,node.col_offset})
    
    def _check_same_return_values(self, node: ast.IfExp):
        if (
                isinstance(node.body, ast.Name)
                and isinstance(node.orelse, ast.Name)
                and node.body.id == node.orelse.id
            ):
                self.useless_ternary_operator.append({node.lineno,node.col_offset})

    def _check_return_value_none(self, node: ast.IfExp):
        if (
                isinstance(node.body, ast.Name)
                and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.IsNot)
                and isinstance(node.orelse, ast.Constant)
                and node.orelse.value == None
            ):
                self.useless_ternary_operator.append({node.lineno,node.col_offset})
        


class Plugin:
    name = __name__
    version = importlib.metadata.version(__name__)

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[Tuple[int,int,str,Type[Any]],None,None]:
        visitor = Visitor()
        visitor.visit(self._tree)   
        for line, col in visitor.problems:
            yield line, col, MSG, type(self)

        visitor = Visitor_second()
        visitor.visit(self._tree)
        for line, col in visitor.useless_ternary_operator:
            yield line, col, MSG_2, type(self)
