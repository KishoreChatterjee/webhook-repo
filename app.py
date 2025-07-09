from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB setup (adjust if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["github_actions"]
collection = db["events"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    author = ''
    from_branch = ''
    to_branch = ''

    # Handle PUSH event
    if event_type == 'push':
        author = data.get('pusher', {}).get('name')
        to_branch = data.get('ref', '').split('/')[-1]

    # Handle PULL REQUEST event
    elif event_type == 'pull_request':
        pr = data.get('pull_request', {})
        author = pr.get('user', {}).get('login')
        from_branch = pr.get('head', {}).get('ref')
        to_branch = pr.get('base', {}).get('ref')

        if data.get('action') == 'closed' and pr.get('merged'):
            event_type = 'merge'
        else:
            event_type = 'pull_request'

    # Save the event in MongoDB
    event_data = {
        'author': author,
        'action_type': event_type,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'timestamp': datetime.utcnow()
    }
    collection.insert_one(event_data)

    return jsonify({'status': 'success'}), 200

@app.route('/events', methods=['GET'])
def get_events():
    # Get last 10 events from DB
    events = list(collection.find().sort('timestamp', -1).limit(10))
    for event in events:
        event['_id'] = str(event['_id'])  # Convert ObjectId to string
        event['timestamp'] = event['timestamp'].strftime('%d %B %Y - %I:%M %p UTC')
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True)
