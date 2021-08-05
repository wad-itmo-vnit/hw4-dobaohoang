from flask import Flask, render_template, request, send_from_directory, redirect
from flask.helpers import url_for
from flask_socketio import Namespace, emit, SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bimatvclluon'
socketio = SocketIO(app)
IMAGES_ROOT = 'images/'

class ChatNameSpace(Namespace):
    def on_connect(self):
        room_name = request.args.get('room_name', '')
        join_room(room_name)
        print('User connected')
        
        # read data from database
        with open('database.txt','r') as f:
            while True:
                line = f.readline().strip()
                if not line:
                    break
                username, message, room, timestamp = line.split(';')
                if room == room_name:
                    emit('server_message', {
                        'username':username, 
                        'message': message,
                        'timestamp': timestamp,
                    })
            f.close()
    
    def on_disconnect(self):
        room_name = request.args.get('room_name', '')
        leave_room(room_name)
        print('User disconnected')

    def on_client_message(self, data):
        username = request.args.get('username', '')
        room_name = request.args.get('room_name', '')
        message = data.get('message', '')
        timestamp = data.get('timestamp', '')

        # save message to database
        with open('database.txt','a') as f:
            f.write(username + ';' + message + ';' + room_name + ';'+ timestamp +'\n')
            f.close()

        emit('server_message', {'username':username, 'message': message}, to=room_name)

socketio.on_namespace(ChatNameSpace('/chat'))

@app.route('/chat/', methods=['GET'])
def chat():
    username = request.args.get('username', '')
    room_name = request.args.get('room_name','')

    return render_template('test.html', username=username, room_name=room_name)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', '')
        room_name = request.form.get('room_name', '')
        return redirect(url_for('chat', username=username, room_name=room_name))

    return render_template('index.html')

@app.route('/images/<path:filename>')
def image_file(filename):
    return send_from_directory(IMAGES_ROOT, filename, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app)