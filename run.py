import os
from design import app

port_value = int(os.environ.get('PORT', 5000))
app.run('0.0.0.0',port=port_value)
