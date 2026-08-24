import os
import sys
#
from epic import (
    epics_vipergpt,
    imgpatch
)
from opal_checker import immut

class GQAMutationChecker:
    def __init__(self, program: str, filename: str, image: imgpatch.WrappedImage, ASYNC=False):
        self.program = program
        self.filename = filename
        self.image = image
        self.ASYNC = ASYNC
    
    def _get_py_exec_command(self, py_code):
        exec_globals = {
            "__builtins__": __builtins__,
            "ImagePatch": imgpatch.ImagePatchAsync if self.ASYNC else imgpatch.ImagePatch,
            "bool_to_yesno": epics_vipergpt.bool_to_yesno,
            **immut.GLOBALS
        }

        code = compile(py_code, filename=self.filename, mode='exec')
        exec_locals = {}
        exec(code, exec_globals, exec_locals)

        return exec_locals.get("execute_command")
        
    def exec(self):
        try:
            source_inlined = immut.inline_literals(self.program)
            execute_command = self._get_py_exec_command(source_inlined)
            result = execute_command(self.image)
        except Exception:
            raise

class AgentDojoMutationChecker:
    def __init__(self, program: str, filename: str, exec_globals: dict):
        self.program = program
        self.filename = filename
        self.exec_globals = exec_globals

    def _get_py_exec_command(self, py_code):
        code = compile(py_code, filename=self.filename, mode='exec')
        exec_locals = {}
        exec(code, self.exec_globals, exec_locals)

        return exec_locals.get("execute_command")

    def exec(self):
        try:
            source_inlined = immut.inline_literals(self.program)
            execute_command = self._get_py_exec_command(source_inlined)
            result = execute_command()
        except Exception:
            raise