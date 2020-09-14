# -*- coding: utf-8 -*-
import os
import json
import requests

from flask import Flask, render_template, redirect, request, Response

app = Flask(__name__)


def validate(params):
    if params["event"]["type"] != "message":
        print("Event type is ", params["event"]["type"], "but not `message`")

    app_id = params["api_app_id"] == os.environ["APP_ID"]
    token = params["token"] == os.environ["VERIFICATION_TOKEN"]
    team = params["team_id"] == os.environ["TEAM_ID"]
    channel = params["event"]["channel"] == os.environ["USLACKBOT_CHANNEL"]
    user = params["event"].get("user", "") == "USLACKBOT"
    subtype = params["event"]["subtype"] = "file_share"

    if app_id and token and team and channel and user and subtype:
        return True
    else:
        if not app_id:
            print("APP_ID is not right!")
        if not token:
            print("TOKEN is not right!")
        if not team:
            print("TEAM_ID is not right!")
        if not channel:
            print("USLACKBOT channel is not right!")
        print("\n\n\n")
        return False


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "GET":
        return redirect("https://github.com/kossiitkgp/email-to-slack")
    elif request.method == "POST":

        print("New Email recieved\n Parameters")
        params = request.get_json(force=True)
        print(json.dumps(params))
        print("\n\n\n\nHEADERS\n\n\n\n")
        print(request.headers)
        """
        Enable this to verify the URL while installing the app
        """
        if 'challenge' in params:
            data = {
                'challenge': params.get('challenge'),
            }
            resp = Response(
                response=json.dumps(data),
                status=200,
                mimetype='application/json'
            )
            resp.headers['Content-type'] = 'application/json'

            return resp
        if validate(params):
            email = params["event"]["files"][0]

            if f"CHECKED_{email['id']}" in os.environ or "X-Slack-Retry-Num" in request.headers:
                # This email has already been processed
                return Response(response="Duplicate", status=409)

            

            dataTosend = {
                "token": os.environ["USER_TOKEN"],
                "channel": os.environ["SEND_TO_CHANNEL"],
                "text": "<" + email["permalink"] + ">",
                "as_user": True,
                "unfurl_links": True
                
            }

            INCOMING_WEBHOOK_URL = os.environ["INCOMING_WEBHOOK_URL"]

            headers = {
                "Content-type": "application/json"
            }
            print("Sending the following data to ", INCOMING_WEBHOOK_URL)
            print("\n\n\n", dataTosend ,"\n\n\n")
            r = requests.post("https://slack.com/api/chat.postMessage", headers=headers, params=dataTosend)

            print("\n\n\n Exit with status code {}\n\n".format(r.status_code))
            # Slack API sends two payloads for single event. This is a bug
            # involving Heroku and Slack API.
            os.environ[f"CHECKED_{email['id']}"] = ''

            return Response(
                response="ok",
                status=200
            )
        else:
            return Response(
                response="Bad request",
                status=401
            )


app.secret_key = os.environ.setdefault("APP_SECRET_KEY", "notsosecret")
app.config['SESSION_TYPE'] = 'filesystem'

app.debug = False

if __name__ == '__main__':
    app.run(debug=True)
