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
        port=configuration["database_port"]
      )
      self.cursor = self.connection.cursor()
      configuration["database"] = self
    except psycopg2.ConnectionException as error:
      print("Unable to connect: ", error)
      sys.exit()

  def __del__(self):
    self.connection.close()

database = Database()
