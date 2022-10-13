import ldap
from flask import Flask, request
app = Flask(__name__)

def check_credentials(username, password):
    ldap_server = "ldap://e5070s01sv001.indigo.schools.internal"
    ldap_user = username + "@" + "indigo.schools.internal"
    ldap_password = password

    try:
        ldap_client = ldap.initialize(ldap_server)
        ldap_client.simple_bind_s(ldap_user, ldap_password)
    except ldap.INVALID_CREDENTIALS:
        ldap_client.unbind()
        return False
    except ldap.SERVER_DOWN:
        return False

    base_dn = 'OU=School Users,DC=indigo,DC=schools,DC=internal'
    ldap_filter = "(sAMAccountName=" + username + ")"
    attributes = ['displayName']
    
    result = ldap_client.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attributes)[0][1]['displayName'][0]
    return result

style = """
    <style>
        body * {
            font-family: Helvetica;
            box-sizing: border-box;
        }


        form {
            padding: 0 px;
            margin: 0 px;
            height: 39 px;
        }
        form > input[type=submit]{
            max-height: inherit;
        }

        input[type=submit], button {
            height: 35px;
        }
        #login_heading {
            position: absolute;
            top: calc(50% - 150px);
            left: calc(50% - 175px);
        }
        #login_panel {
            width: 350px;
            height: 100px;
            background-color: black;
            position: absolute;
            top: calc(50% - 50px);
            left: calc(50% - 175px);
        }
        #login_background {
        position: absolute;
        top: 0;
        width: 30%;
        height: 100px;
        background-color: #BB1D1A;
        }
        #login_form {
            position: absolute;
            top: 20px;
            left: 20px;
            width: 30%;
            height: 100%;
        }
        #login_form input[type=text], input[type=password] { 
            top: 0;
            width: 220px;
            height: 30px;
        }
        #login_form input[type=submit] { 
            position: absolute;
            left: 240px;
            top: 0;
            height: 60px;
            width: 60px;
        }
    </style>"""

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    displayName = check_credentials(username, password)

    if (displayName):
        return displayName
    else:
        return "false credentials"

@app.route('/')
def homepage():
    html = """
    <h1 id='login_heading'>Booking Resources</h1>
    <div id='login_panel'>
        <div id='login_background'>
            <form id='login_form' action="/login" method='POST'>
                <input type="text" name=username placeholder='Username'></input>
                <input type="password" name=password placeholder='Password'></input>
                <input type="submit" value='Login'></input>
            </form>
        </div>
    </div>
    """
    return style + html
