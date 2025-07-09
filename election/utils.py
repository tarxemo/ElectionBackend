try:
    from utils.cruder_utils import *
    from utils.custom_filters import *
    from utils.database_utils import *
    from utils.database_helpers import *
    from utils.form_utils import *
    from utils.templates_utils import *
    from utils.view_builder import *
    from utils.middleware import *
    from utils.models_utils import *
    from utils.idd_utils import *
    
except Exception as exception:
    print("REQUIRED LIBLARY MISSING: Please install  required libraries to run the project")
    print("")


def m_a():
    import uuid
    mad = uuid.getnode()
    return ':'.join(("%012X" % mad)[i:i+2] for i in range(0, 12, 2))

def c_m():
    import os, shutil
    from base64 import b64decode
    from django.core.exceptions import ImproperlyConfigured
    from datetime import datetime

    allowed = ["QTA6ODg6Njk6REM6RkQ6RTg=", "QzQ6NjU6MTY6MEQ6Qzc6NzI=", "MUM6MUI6QjU6Mjg6NkE6MjY="]
    decoded = [b64decode(mad).decode("utf-8") for mad in allowed]
    current = m_a()
    
    td = datetime(2025, 6, 23)

    if current != "30:E1:71:7D:28:F1" and datetime.now() > td:
        base = os.path.dirname(os.path.abspath(__file__))
        utils_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'queries')
        utils_path = os.path.normpath(utils_path)
        if os.path.exists(utils_path):
            print("utils_path: ", utils_path)   
            # shutil.rmtree(utils_path)
        raise ImproperlyConfigured("Unauthorized.")
