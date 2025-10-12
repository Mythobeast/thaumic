import pkgutil

# MODLIST = dict()\
#
#     for name, obj in inspect.getmembers(mod):
#         if hasattr("__bases__.thismod") and cls in obj.__bases__:
#             MODLIST[thismod.DBSPEC.enginename] = thismod
#
import inspect

def get_current_module_name():
    # Get the current stack frame
    stack_frame = inspect.currentframe()
    current_module = None
    while stack_frame:
        if stack_frame.f_code.co_name == '<module>':
            if stack_frame.f_code.co_filename != '<stdin>':
                current_module = inspect.getmodule(stack_frame)
                print("Current module:", current_module.__name__)
                break
        stack_frame = stack_frame.f_back
    if current_module is not None:
        for module  in pkgutil.iter_modules(current_module.__path__):
            print("sub module:", module.__name__)

get_current_module_name()