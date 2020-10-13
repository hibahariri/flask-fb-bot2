from flask import Blueprint

Test_api = Blueprint('Test_api', __name__)


@Test_api.route("/Test")
def Testlist():
    print("done")
    return "list of accounts"
