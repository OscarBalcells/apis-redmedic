# APIs
Provider Flask RestAPI which serves as a database

# Usage
You'll need Docker Compose as well as Docker to run the APIs. There's three of them in the sample data as there are three providers in the beta of the system to showcase its functionality. The providers run therefore on localhost with ports 5000, 5001 and 5002.

There's 3 different Flask resources you can access.

1) Nonce

Every single request is protected against replay attacks because the transaction gets sent with a nonce. The nonce is just an integer value representing how many transactions that particular address has sent. The signature includes the nonce and once the transaction is processed by the API, the valid nonce now will be the previous nonce plus 1. nonce_now = nonce_before + 1 after transaction gets processed. Any data requestor will therefore either have to keep track of the valid nonce or ask the API using the following resource:

***<string:host>:<int:port>/nonce/<string:id>&<string:sig>***

Whereas the id is the identifier of the patient and the signature is string representing the signed message "nonce". We basically sign the word "nonce" and send it. The API can then recover the address which signed the message using the following commands:

'''
from eth_account.messages import encode_defunct
from web3 import Web3, HTTPProvider
w3 = Web3(HTTPProvider(my_geth_node))

messageHash = encode_defunct(text="nonce")
addr = w3.eth.account.recover_message(messageHash, signature=sig)
'''

2) Patient Info

Next is command for querying info about a patient. We have to specify the id of the patient as well as the category we want to query as well as the valid nonce. If we don't know the nonce we can just query the previous Resource.

***<string:host>:<int:port>/patient/<string:id>&<string:category>&<string:nonce>&<string:sig>***

If we write "all" as category, the whole profile will be sent.
If a valid category is specified, only the list of resources of that category will be sent.

3) Edit Info

***<string:host>:<int:port>/edit***

Here, the whole profile of a patient will be attached in the body of the http request with the JSON format. The API will therefore just tell the database the following command db[patient_id] = attached_json

The fields of a patient_id object stored in the database are:

personalData = {"id":"", "name":"", "mphr":"", pphr:""}
allergies = []
procedures = []
immunizations = []
medications = []
conditions = []
images = []

## How to sign a request?

'''
//data is a javascript String
function signData(data) {
    const msgBuffer = ethUtil.toBuffer(data);
		const msgHash = ethUtil.hashPersonalMessage(msgBuffer);
		const privateKey = new Buffer(this.privKey, "hex"); //raw private key stored in the same class
		const sig = ethUtil.ecsign(msgHash, privateKey);
		const sigHex = "0x"+sig.r.toString("hex")+sig.s.toString("hex")+sig.v.toString(16);
    return sigHex;
}
'''


