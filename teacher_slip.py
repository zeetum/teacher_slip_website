# flask --app teacher_slip.py run --host=0.0.0.0
import ldap
import csv
from flask import Flask, request, redirect
from datetime import date

today = date.today().strftime("%d/%m/%Y")

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
    
    teacher_details = ldap_client.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attributes)[0][1]['displayName'][0]
    teacher_details = teacher_details.decode('utf-8').title().split()
    teacher_details.reverse()
    return " ".join(teacher_details)

# returns a dict in the form"
#   "Room 1": ["Fred", "Larry", "Sam"]
def get_room_students(file_path):
    with open(file_path, newline='') as csvfile:
        student_csv = csv.reader(csvfile)
        next(student_csv)
        students = {}
        for student_details in student_csv:
            students.setdefault(student_details[10], []).append(student_details[2] + " " + student_details[4])

        for s in students.values():
            s = s.sort()
            
        return students
            

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    teacher = check_credentials(username, password)
    students = get_room_students('/run/user/1000/gvfs/smb-share:server=e5070s01sv001,share=rmms/Keys/Integris/Outbox/Student.csv')

    if (teacher):

        datalists = """
        <datalist id="rooms_list">
            <option value="Other"></option>"""
        for room in students.keys():
            datalists += "<option value='" + room + "'></option>"
        datalists += """</datalist>
        <datalist id="students_list">"""
        for rooms in students.values():
            for student in rooms:
                datalists += "<option value='" + student + "'></option>"         
        datalists += """</datalist>"""
        
        html = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Teacher Minor Behavior Slip</title>
            </head>
            <script  type="text/javascript">"""

        room_strings = []
        for room in students.keys():
            students_array = "'" + room + "':["
            students_array += ",".join(f'"{s}"' for s in students[room])
            students_array += "]"
            room_strings.append(students_array)
        html += " students = {" + ",".join(room_strings) + "}; "

        html += """document.addEventListener("DOMContentLoaded", function() {
                    // Alternate colours for Behavior columns
                    let column = true
                    for (let behaviors of document.getElementsByClassName("sub_behavior_details")) {
                        column = !column
                        let row = column
                        for (let item of behaviors.getElementsByClassName("behavior_option")) {
                            if (row == true) {
                                item.style.backgroundColor = '#EBEBEB'
                            } else {
                                item.style.backgroundColor = '#F8F8FF'
                            }
                            row = !row
                        }
                    }
                    // Click on label toggles checkbox
                    for (let input of document.getElementsByTagName("input")) {
                        if (input.type === "checkbox") {
                            input.parentElement.parentElement.addEventListener("click",function( {target} ) {
                                if(target.matches("input[type=checkbox]")) { return }
                                let checkbox = input.parentElement.getElementsByTagName('input')[0];
                                checkbox.checked = !checkbox.checked
                            });
                        }
                    }

                    
                    // Populate student field based on room selection
                    document.getElementById("room_search_field").addEventListener("input", function () {
                        let students_list = document.getElementById("students_list")
                        
                        while (students_list.options.length > 0) {
                            students_list.children[0].remove()
                        }

                        if (this.value == "Other") {
                            for (let class_student of Object.values(students)) {
                                for (let student of class_student) {
                                    var option = document.createElement('option');
                                    option.value = student;
                                    students_list.appendChild(option);
                                }
                            }
                        } else {
                            for (let student of students[this.value]) {
                                var option = document.createElement('option');
                                option.value = student;
                                students_list.appendChild(option);
                            }
                        }
                    });
                });
            </script>

            <style>
                html * {
                    font-family: Arial !important;
                }

                #teacher_header {
                    height: 50px;
                    width: 900px;
                    margin: auto;
                    background-color: #EBEBEB;
                    border-top-left-radius: 15px;
                    border-top-right-radius: 15px;
                }
                #teacher_header #teacher_name {
                    line-height: 50px;
                    padding-left: 5px;
                    font-size: 30px;
                }
                #teacher_header #form_name {
                    line-height: 50px;
                    padding-right: 5px;
                    float: right;
                }

                #minor_slip_form {
                    width: 900px;
                    margin: auto;
                    
                }

                #incident_details {
                    height: 27px;
                    width: 900px;
                    float: left;
                    overflow: hidden;
                }
                
                #incident_details div {
                    height: 25px;
                    width: 298px;
                    float: left;
                    display: flex;
                }
                #incident_details div .label_div {
                    height: 100%;
                    width: 100px;
                    padding-left: 5px;
                    align-items: center;
                    float: left;
                    background-color: #EBEBEB;
                }
                #incident_details div .input_div {
                    height: 100%;
                    width: 200px;
                    align-items: center;
                    float: left;
                    background-color: #F8F8FF;
                }
                #incident_details div .input_div input {
                    width: 100%;
                }

                #location_details {
                    width: 600px;
                    float: left;
                    box-sizing: border-box;
                    border: solid;
                    overflow: hidden;
                }
                #location_details .heading {
                    height: 15px;
                    width: 600px;
                    padding: 5px;
                    background-color: #EBEBEB;
                    border-bottom: solid;
                }
                #location_details .heading span {
                    padding-left: 5px;
                }
                #location_details div {
                    height: 25px;
                    width: 198px;
                    float: left;
                    display: flex;
                }
                #location_details > :nth-child(even) {
                    background-color: #EBEBEB;
                }
                #location_details > :nth-child(odd) {
                    background-color: #F8F8FF;
                }
                #location_details div .label_div {
                    height: 100%;
                    width: 175px;
                    padding-left: 5px;
                    align-items: center;
                    float: left;
                }
                #location_details div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                }

                #time_details {
                    width: 300px;
                    float: left;
                    box-sizing: border-box;
                    border: solid;
                    overflow: hidden;
                }
                #time_details .heading {
                    height: 15px;
                    width: 300px;
                    padding: 5px;
                    background-color: #EBEBEB;
                    border-bottom: solid;
                }
                #time_details .heading span {
                    padding-left: 15px;
                }
                #time_details div {
                    height: 25px;
                    width: 300px;
                    float: left;
                    display: flex;
                }
                #time_details > :nth-child(odd) {
                    background-color: #EBEBEB;
                }
                #time_details > :nth-child(even) {
                    background-color: #F8F8FF;
                }
                #time_details div .label_div {
                    height: 100%;
                    width: 275px;
                    padding-left: 5px;
                    align-items: center;
                    float: left;
                }
                #time_details div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                }

                #behavior_details {
                    width: 900px;
                    float: left;
                    box-sizing: border-box;
                    border-left: solid;
                    border-bottom: solid;
                    border-right: solid;
                    overflow: hidden;
                }
                #behavior_details .heading {
                    height: 15px;
                    width: 900px;
                    padding: 5px;
                    background-color: #F8F8FF;
                }
                #behavior_details .heading span {
                    padding-left: 15px;
                }
                #behavior_details > .heading {
                    height: 15px;
                    width: 900px;
                    padding: 5px;
                    background-color: #EBEBEB;
                }
                .sub_behavior_details {
                    width: 223px;
                    float: left;
                }
                .sub_behavior_details .heading {
                    height: 20px;
                    width: 225px;
                    background-color: #EBEBEB;
                    border-bottom: solid;
                }
                .sub_behavior_details div {
                    height: 25px;
                    width: 225px;
                    float: left;
                    display: flex;
                }
                .sub_behavior_details div .label_div {
                    height: 100%;
                    width: 275px;
                    padding-left: 5px;
                    align-items: center;
                    float: left;
                }
                .sub_behavior_details div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                }
                #teacher_actions {
                    width: 300px;
                    height: 230px;
                    float: left;
                    box-sizing: border-box;
                    border-left: solid;
                    border-bottom: solid;
                    border-right: solid;
                    overflow: hidden;
                }
                #teacher_actions .heading {
                    height: 15px;
                    width: 300px;
                    padding: 5px;
                    background-color: #F8F8FF;
                }
                #teacher_actions .heading span {
                    padding-left: 15px;
                }
                #teacher_actions > .heading {
                    height: 15px;
                    width: 300px;
                    padding: 5px;
                    background-color: #EBEBEB;
                }
                
                #step_1 {
                    width: 300px;
                    float: left;
                }
                #step_1 > :nth-child(odd) {
                    background-color: #EBEBEB;
                }
                #step_1 > :nth-child(even) {
                    background-color: #F8F8FF;
                }
                #step_1 .heading {
                    border-top: solid
                }
                #step_1 > div {
                    height: 25px;
                    width: 300px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_1 > div .label_div {
                    height: 100%;
                    width: 275px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_1 > div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_2 {
                    width: 300px;
                    float: left;
                    border-top: solid;
                }
                #step_2 > :nth-child(odd) {
                    background-color: #EBEBEB;
                }
                #step_2 > :nth-child(even) {
                    background-color: #F8F8FF;
                }
                #step_2 > div {
                    height: 25px;
                    width: 300px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_2 > div .label_div {
                    height: 100%;
                    width: 275px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_2 > div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }

                #behavior_concequences {
                    width: 600px;
                    height: 230px;
                    float: left;
                    box-sizing: border-box;
                    border-left: solid;
                    border-bottom: solid;
                    border-right: solid;
                    overflow: hidden;
                }
                #behavior_concequences .heading {
                    height: 15px;
                    width: 295px;
                    padding: 5px;
                    background-color: #F8F8FF;
                }
                #behavior_concequences > .heading {
                    height: 15px;
                    width: 595px;
                    padding: 5px;
                    background-color: #EBEBEB;
                    border-bottom: solid;
                }
                #step_3_classroom {
                    width: 300px;
                    float: left;
                    border-right: solid;
                }
                #step_3_classroom > :nth-child(even) {
                    background-color: #EBEBEB;
                }
                #step_3_classroom > :nth-child(odd) {
                    background-color: #F8F8FF;
                }
                #step_3_classroom > div {
                    height: 25px;
                    width: 300px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_3_classroom > div .label_div {
                    height: 100%;
                    width: 275px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_3_classroom > div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_3_classroom > .heading {
                    height: 15px;
                    width: 290px;
                    padding: 5px;
                }
                #step_3_playground {
                    width: 290px;
                    float: left;
                }
                #step_3_playground > :nth-child(odd) {
                    background-color: #EBEBEB;
                }
                #step_3_playground > :nth-child(even) {
                    background-color: #F8F8FF;
                }
                #step_3_playground > div {
                    height: 25px;
                    width: 300px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_3_playground > div .label_div {
                    height: 100%;
                    width: 275px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_3_playground > div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_4 > .heading {
                    height: 15px;
                    width: 295px;
                    padding: 5px;
                }
                
                #step_4 {
                    width: 600px;
                    float: left;
                    border-left: solid;
                    border-bottom: solid;
                    border-right: solid;
                }
                #step_4 > :nth-child(odd) {
                    background-color: #EBEBEB;
                }
                #step_4 > :nth-child(even) {
                    background-color: #F8F8FF;
                }
                #step_4 > div {
                    height: 25px;
                    width: 600px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_4 > div .label_div {
                    height: 100%;
                    width: 575px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_4 > div .input_div {
                    height: 100%;
                    width: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #step_4 > .heading {
                    height: 15px;
                    width: 590px;
                    padding: 5px;
                }

                #contact_admin {
                    width: 291px;
                    height: 75px;
                    float: left;
                    border-bottom: solid;
                    border-right: solid;
                    background-color: #EBEBEB;
                }
                #contact_admin .label_div {
                    height: 100%;
                    width: 207px;
                    font-size: 25px;
                    font-weight: bold;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #contact_admin .input_div {
                    height: 100%;
                    width: 45px;
                    padding-left: 25px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #contact_admin input[type=checkbox] {
                    transform: scale(2);
                    padding: 10px;
                }
                #contact_admin div {
                    height: 100%;
                    width: 300px;
                    align-items: center;
                    float: left;
                    display: flex;
                }
                #padding_div {
                    width: 600px;
                    height: 20px;
                    float: left;
                }
                #comments {
                    height: 130px;
                    width: 895px;
                    float: left;
                    border: solid;
                }
                #comments .heading {
                    height: 20px;
                    width: 885px;
                    padding: 5px;
                    float: left;
                    background-color:#EBEBEB;
                }
                #comments textarea {
                    padding-left: 5px;
                    height: 93px;
                    width: 885px;
                    float: left;
                }
                input[type=submit] {
                    height: 50px;
                    width: 900px;
                    float: left;
                    font-size: 30px;
                }
            </style>

            <body>
                <div id=teacher_header>
                    <span id="teacher_name">""" + teacher + """</span> <span id="form_name">Student Minor Behavior Slip</span>
                </div>""" + datalists + """
                
                <form id="minor_slip_form" action="/submit_form">
                    <input type="hidden" name="teacher_name" value='""" + teacher + """'>
                    <div id=incident_details>
                        <div>
                            <div class="label_div">
                                <label for="room">Room</label>
                            </div>
                            <div class="input_div">
                                <input id="room_search_field" type="search" name="room" list="rooms_list">
                            </div>
                        </div>
                        <div>
                            <div class="label_div">
                                <label for="student">Student</label>
                            </div>
                            <div class="input_div">
                                <input id="student_search_field" type="search" name="student" list="students_list">
                            </div>
                        </div>
                        <div>
                            <div class="label_div">
                                <label for="date">Date</label>
                            </div>
                            <div class="input_div">
                                <input type="text" name="date" value='""" + today + """'>
                            </div>
                        </div>
                    </div>

                    <div id=location_details>
                        <div class="heading"><span>Location</span></div>

                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="classroom">
                            </div>
                            <div class="label_div">
                                <label for="classroom">Classroom</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="front_quiet">
                            </div>
                            <div class="label_div">
                                <label for="front_quiet">Front Quiet</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="nature_play">
                            </div>
                            <div class="label_div">
                                <label for="nature_play">Nature Play</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="play_equipment">
                            </div>
                            <div class="label_div">
                                <label for="play_equipment">Play Equipment</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="sand_pit">
                            </div>
                            <div class="label_div">
                                <label for="sand_pit">Sand Pit</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="pp_playground">
                            </div>
                            <div class="label_div">
                                <label for="pp_playground">PP Playground</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="music">
                            </div>
                            <div class="label_div">
                                <label for="music">Music</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="languages">
                            </div>
                            <div class="label_div">
                                <label for="languages">Languages</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="art">
                            </div>
                            <div class="label_div">
                                <label for="art">Art</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="phys_ed">
                            </div>
                            <div class="label_div">
                                <label for="phys_ed">Phys Ed</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="science">
                            </div>
                            <div class="label_div">
                                <label for="science">Science</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="library">
                            </div>
                            <div class="label_div">
                                <label for="library">Library</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="library_grass">
                            </div>
                            <div class="label_div">
                                <label for="library_grass">Library Grass</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="fitness">
                            </div>
                            <div class="label_div">
                                <label for="fitness">Daily Fitness</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="assembly">
                            </div>
                            <div class="label_div">
                                <label for="assembly">Assembly</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="toilets">
                            </div>
                            <div class="label_div">
                                <label for="toilets">Toilets</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="gazebo">
                            </div>
                            <div class="label_div">
                                <label for="gazebo">Gazebo</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="under_cover">
                            </div>
                            <div class="label_div">
                                <label for="under_cover">Under Cover</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="green_patch">
                            </div>
                            <div class="label_div">
                                <label for="green_patch">Green Patch</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="verandah">
                            </div>
                            <div class="label_div">
                                <label for="verandah">Verandah</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="basketball">
                            </div>
                            <div class="label_div">
                                <label for="basketball">Basketball</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="oval">
                            </div>
                            <div class="label_div">
                                <label for="oval">Oval</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="transition">
                            </div>
                            <div class="label_div">
                                <label for="transition">Transition</label>
                            </div>
                        </div>
                        <div class="location_option">
                            <div class="input_div">
                                <input type="checkbox" name="excersion">
                            </div>
                            <div class="label_div">
                                <label for="excersion">Excursion</label>
                            </div>
                        </div>
                    </div>

                    <div id=time_details>
                        <div class="heading">Time</div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time1">
                            </div>
                            <div class="label_div">
                                <label for="time1">Before School</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time2">
                            </div>
                            <div class="label_div">
                                <label for="time2">8:50 - 10:20</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time3">
                            </div>
                            <div class="label_div">
                                <label for="time3">Recess</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time4">
                            </div>
                            <div class="label_div">
                                <label for="time4">10:40 - 11:40</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time5">
                            </div>
                            <div class="label_div">
                                <label for="time5">11:40 - 12:40</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time6">
                            </div>
                            <div class="label_div">
                                <label for="time6">Lunch</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time7">
                            </div>
                            <div class="label_div">
                                <label for="time7">1:20 - 3:00</label>
                            </div>
                        </div>
                        <div class="time_option">
                            <div class="input_div">
                                <input type="checkbox" name="time8">
                            </div>
                            <div class="label_div">
                                <label for="time8">After School</label>
                            </div>
                        </div>
                    </div>

                    <div id=behavior_details>
                        <div class="heading">Behavior</div>
                        <div class="sub_behavior_details">
                            <div class="heading">Be Responsible</div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="unprepared">
                                </div>
                                <div class="label_div">
                                    <label for="unprepared">Unprepared</label>
                                </div>
                                
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="poor_language">
                                </div>
                                <div class="label_div">
                                    <label for="poor_language">Poor Language</label>
                                </div>

                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="late">
                                </div>
                                <div class="label_div">
                                    <label for="late">Late to Class</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="work_avoidance">
                                </div>
                                <div class="label_div">
                                    <label for="work_avoidance">Work Avoidance</label>
                                </div>
                                
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="off_task">
                                </div>
                                <div class="label_div">
                                    <label for="off_task">Off Task</label>
                                </div>
                            </div>
                        </div>
                        <div class="sub_behavior_details">
                            <div class="heading">Be Respectful</div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="instructions">
                                </div>
                                <div class="label_div">
                                    <label for="instructions">Instructions</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="disrupting_class">
                                </div>
                                <div class="label_div">
                                    <label for="disrupting_class">Disrupting Class</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="calling_out">
                                </div>
                                <div class="label_div">
                                    <label for="calling_out">Calling Out</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="talking_back">
                                </div>
                                <div class="label_div">
                                    <label for="talking_back">Talking Back</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="property_misuse">
                                </div>
                                <div class="label_div">
                                    <label for="property_misuse">Property Misuse</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="tech_misuse">
                                </div>
                                <div class="label_div">
                                    <label for="tech_misuse">Tech Misuse</label>
                                </div>
                            </div>
                        </div>
                        <div class="sub_behavior_details">
                            <div class="heading">Be Caring</div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="poor_behavior">
                                </div>
                                <div class="label_div">
                                    <label for="poor_behavior">Poor Behavior</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="physical_contact">
                                </div>
                                <div class="label_div">
                                    <label for="physical_contact">Physical Contact</label>
                                </div>
                            </div>
                        </div>
                        <div class="sub_behavior_details">
                            <div class="heading">Be Your Best</div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="dress_code">
                                </div>
                                <div class="label_div">
                                    <label for="dress_code">Dress Code</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="inattentive">
                                </div>
                                <div class="label_div">
                                    <label for="inattentive">Inattentive</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="lacks_application">
                                </div>
                                <div class="label_div">
                                    <label for="lacks_application">Lacks Application</label>
                                </div>
                            </div>
                            <div class="behavior_option">
                                <div class="input_div">
                                    <input type="checkbox" name="dishonesty">
                                </div>
                                <div class="label_div">
                                    <label for="dishonesty">Dishonesty</label>
                                </div>  
                            </div>
                        </div>
                    </div>

                    <div id=teacher_actions>
                        <div class="heading">Teacher Actions</div>
                        <div id="step_1">
                            <div class="heading">Step 1</div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="low_key_response">
                                </div>
                                <div class="label_div">
                                    <label for="low_key_response">Low Key Response</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="redirect">
                                </div>
                                <div class="label_div">
                                    <label for="redirect">Redirect</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="teach">
                                </div>
                                <div class="label_div">
                                    <label for="teach">Teach</label>
                                </div>
                            </div>
                        </div>
                        <div id="step_2">
                            <div class="heading">Step 2</div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="provide_choice">
                                </div>
                                <div class="label_div">
                                    <label for="provide_choice">Provide Choice</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="student_confrence">
                                </div>
                                <div class="label_div">
                                    <label for="student_confrence">Student Confrence</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div id=behavior_concequences>
                        <div class="heading">Behavior Consequences</div>
                        <div id="step_3_classroom">
                            <div class="heading">Step 3 - Classroom</div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="explicit_classroom">
                                </div>
                                <div class="label_div">
                                    <label for="explicit_classroom">Explicit Teaching</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="isolation">
                                </div>
                                <div class="label_div">
                                    <label for="isolation">Isolation</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="loss_of_privilege_classroom">
                                </div>
                                <div class="label_div">
                                    <label for="loss_of_privilege_classroom">Loss of Privilege</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="partner_referral">
                                </div>
                                <div class="label_div">
                                    <label for="partner_referral">Partner Room Referral</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="parent_notification">
                                </div>
                                <div class="label_div">
                                    <label for="parent_notification">Parent Notification</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="parent_meeting">
                                </div>
                                <div class="label_div">
                                    <label for="parent_meeting">Parent Meeting</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="informal_contract">
                                </div>
                                <div class="label_div">
                                    <label for="informal_contract">Informal Contract</label>
                                </div>
                            </div>
                        </div>
                        <div id="step_3_playground">
                            <div class="heading">Step 3 - Playground</div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="explicit_playground">
                                </div>
                                <div class="label_div">
                                    <label for="explicit_playground">Explicit Teaching</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="sit_out_of_play">
                                </div>
                                <div class="label_div">
                                    <label for="sit_out_of_play">Sit out of play</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="walk_with_teacher">
                                </div>
                                <div class="label_div">
                                    <label for="walk_with_teacher">Walk with Teacher</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="loss_of_privilege_playground">
                                </div>
                                <div class="label_div">
                                    <label for="loss_of_privilege_playground">Loss of Privilege</label>
                                </div>
                            </div>
                            <div>
                                <div class="input_div">
                                    <input type="checkbox" name="on_bell_issue">
                                </div>
                                <div class="label_div">
                                    <label for="on_bell_issue">On bell Issue</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div id="step_4">
                        <div class="heading">Step 4 - 3-5 slips ine one week means admin action required</div>
                        <div>
                            <div class="input_div">
                                <input type="checkbox" name="major_form_required">
                            </div>
                            <div class="label_div">
                                <label for="major_form_required">Major Behavior Required</label>
                            </div>
                        </div>
                        <div>
                            <div class="input_div">
                                <input type="checkbox" name="admin_action_required">
                            </div>
                            <div class="label_div">
                                <label for="admin_action_required">Admin Action Required</label>
                            </div>
                        </div>
                    </div>
                    <div id="contact_admin">
                        <div class="input_div">
                            <input type="checkbox" name="contact_admin">
                        </div>
                        <div class="label_div">
                            <label for="contact_admin">Admin Follow Up</label>
                        </div>
                    </div>

                    <div id="padding_div"></div>

                    <div id="comments">
                        <div class="heading">Additional Comments</div>
                        <textarea name="addtional_comments"></textarea>
                    </div>
                    
                    <div id="padding_div"></div>

                    <input type="submit" value="Submit to Admin">
                </form>
            </body>
        </html>

        """

        return html
    else:
        return redirect("/")

@app.route('/')
def homepage():
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
