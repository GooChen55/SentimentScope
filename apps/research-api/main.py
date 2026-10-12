
import  uvicorn

from app import  app
from  engines.contracts import  config

if __name__ == "__main__":
    uvicorn.run(app.app,host=config.get_settings().HOST,port=config.get_settings().PORT)
