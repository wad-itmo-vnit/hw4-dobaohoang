from flask import Flask, render_template, request, send_from_directory, redirect
from flask.helpers import url_for
from flask_socketio import Namespace, emit, SocketIO, join_room, leave_room, send
import bot

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bimatvclluon'
socketio = SocketIO(app)
IMAGES_ROOT = 'images/'

def save_to_database(username, room_name, message, timestamp):
    with open('database.txt','a') as f:
        f.write(username + ';' + message + ';' + room_name + ';'+ timestamp +'\n')
        f.close()

class ChatNameSpace(Namespace):

    def on_connect(self):
        username = request.args.get('username', '')
        room_name = request.args.get('room_name', '')
        join_room(room_name)
        print('User connected')
        
        # read data from database
        with open('database.txt','r') as f:
            while True:
                line = f.readline().strip()
                if not line:
                    break
                user, msg, room, timestamp = line.split(';')
                if room == room_name:
                    emit('server_message', {
                        'username':user, 
                        'message': msg,
                        'timestamp': timestamp,
                    })
            f.close()

        # send greeting smg
        bot_msg = bot.greeting(username, room_name)
        emit('server_message', bot_msg, to=room_name)
        save_to_database(bot_msg['username'], room_name, bot_msg['message'], bot_msg['timestamp'])
    
    def on_disconnect(self):
        username = request.args.get('username', '')
        room_name = request.args.get('room_name', '')
        leave_room(room_name)
        print('User disconnected')

        # send good bye msg
        bot_msg = bot.good_bye(username, room_name)
        emit('server_message', bot_msg, to=room_name)
        save_to_database(bot_msg['username'], room_name, bot_msg['message'], bot_msg['timestamp'])

    def on_client_message(self, data):
        username = request.args.get('username', '')
        room_name = request.args.get('room_name', '')
        message = data.get('message', '')
        timestamp = data.get('timestamp', '')

        save_to_database(username, room_name, message, timestamp)
        emit('server_message', {'username':username, 'message': message}, to=room_name)

        # send answer msg
        bot_msg = bot.answer(username, room_name, message)
        if bot_msg['message']:
            emit('server_message', bot_msg, to=room_name)
            save_to_database(bot_msg['username'], room_name, bot_msg['message'], bot_msg['timestamp'])

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
    print('Server started!')
    socketio.run(app)