import sys
import psycopg2
from util import configuration

class Database:
  __instance = None

  def __init__(self):
    if not Database.__instance is None:
      raise Exception("This class has already been instantiated")
    
    Database.__instance = self
    
    try:
      self.connection = psycopg2.connect(
        database=configuration["database_name"], 
        user=configuration["database_user"], 
        password=configuration["database_password"],
        host=configuration["database_host"], 
        port=configuration["database_port"],
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
      )
      self.cursor = self.connection.cursor()
      configuration["database"] = self
      print("Database connection established")
      print(self.cursor)
    except Exception as error:
      print("Unable to connect, exiting... ", error)
      sys.exit()

database = Database()
