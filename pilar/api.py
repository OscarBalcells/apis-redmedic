from flask import Flask, request, g
from flask_restful import Resource, Api
import shelve
from web3 import Web3, HTTPProvider
from eth_account.messages import encode_defunct
import sys
import pphrAbi

w3 = Web3(HTTPProvider("https://rinkeby.infura.io"))

app = Flask(__name__)
api = Api(app)
db = None

validCategories = ["all", "personalData", "allergies", "vitals", "medications", "labs", "procedures", "immunizations"]

def get_db(name):
  db = getattr(g, '_database', None)
  db = g._database = shelve.open(name)
  return db

def close_db():
  db = getattr(g, '_database', None)
  db.close()
  db = None

@app.teardown_appcontext
def teardown_db(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

def hasAccess(addr, category, pphrAddr):
  try:
    assert(w3.eth.getCode(pphrAddr) != "0x")
    contract = w3.eth.contract(pphrAddr, abi=pphrAbi.abi)
    hasAccess = contract.functions.hasAccess(addr, w3.toHex(text=category)).call();
    print("Can "+addr+" access category "+category+ " from pphr "+pphrAddr+"? "+str(hasAccess), file=sys.stderr)
    return hasAccess
  except Exception as exc:
    print("Exception ocurred",sys.exc_info()[0],file=sys.stderr)
    return False
  return hasAccess

@app.route("/")
def index():
  return ("Rest API del centro médico Quirón Salud el Pilar")


class Patient(Resource):
  def get(self, id, category, nonce, sig):

    if w3.isConnected() == False:
      print("Not connected", file=sys.stderr)
    else:
      print("It's connected", file=sys.stderr)

    #get address
    message = id + "," + category + "," + nonce
    try:
      messageHash = encode_defunct(text=message)
      addr = w3.eth.account.recover_message(messageHash,signature=sig)
    except:
      return {"ErrorMessage": "Invalid signature provided"}, 402

    #check if nonce is valid
    shelf = get_db("nonces.db")
    keys = list(shelf.keys())

    if addr not in keys:
      shelf[addr] = 0

    if int(nonce) != int(shelf[addr]):
      print("Nonce", nonce, "is invalid, valid nonce is:", shelf[addr], file=sys.stderr)
      return {"ErrorMessage", "Invalid nonce"}, 403

    shelf[addr] += 1
    close_db()

    #check if patient id exists in database
    shelf = get_db("patients.db")
    keys = list(shelf.keys())

    if id not in keys:
      print("Patient not in keys", id, file=sys.stderr)
      return {"ErrorMessage": "Patient not found"}, 404

    #check if address has access to the requested data
    pphrAddr = shelf[id]["personalData"]["pphr"]

    if(hasAccess(addr, category, pphrAddr) == False):
      print("Address", addr, "does not have access", file=sys.stderr)
      return {"ErrorMessage": "Signature doesn't have access to the data!"}, 402
    else:
      print("Address", addr, "has access", file=sys.stderr)

    #return data
    if category != "all":
      try:
        return {"SuccessMessage":"Returning data","data":shelf[id][category]}, 200
      except:
        print("Exception ocurred",sys.exc_info()[0],"invalid category", file=sys.stderr)
        return {"ErrorMessage":"Category not found"}, 404

    return {"SuccessMessage": "Returning the whole profile selected", "data": shelf[id]}, 200

class Nonce(Resource):
  def get(self, id, sig):
    try:
      messageHash = encode_defunct(text="nonce")
      addr = w3.eth.account.recover_message(messageHash, signature=sig)
    except:
      return {"ErrorMessage":"Invalid signature provided"}, 402

    shelf = get_db("nonces.db")
    keys = list(shelf.keys())

    if addr not in keys:
      shelf[addr] = 0

    return {"SuccessMessage": "Returning nonce", "data": shelf[addr]}, 200

class Edit(Resource):

  def get(self):

    args = request.get_json(force=True)

    shelf = get_db("patients.db")
    keys = list(shelf.keys())

    identifier = args["identifier"]
   
    if identifier not in keys:
      return {"ErrorMessage": "Patient not found"}, 404

    return {"SuccessMessage": "Patient found", "data": shelf[identifier]}, 200    

  #put a new patient health record in the database
  def post(self):
    
    args = request.get_json(force=True)

    identifier = args["identifier"]
    record = args["data"]

    shelf = get_db("patients.db")

    shelf[identifier] = record

    return {"SuccessMessage": "Patient record added to database"}, 200

api.add_resource(Nonce, "/nonce/<string:id>&<string:sig>")
api.add_resource(Patient, "/patient/<string:id>&<string:category>&<string:nonce>&<string:sig>")
api.add_resource(Edit, "/edit")
app.run(host="0.0.0.0", port=80, debug=True)
