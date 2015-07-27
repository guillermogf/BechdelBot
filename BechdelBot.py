#!/usr/bin/python
# coding: utf-8

# 2015 © Guillermo Gómez Fonfría <guillermo.gf@openmailbox.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import json
import sys
import time

# Load Token
try:
    token_file = open("token")
except:
    print("Token file missing")
    sys.exit(1)

token = token_file.read().rstrip("\n")
token_file.close()

# Telegram API urls
api_url = "https://api.telegram.org/bot"
token_url = api_url + token
getupdates_url = token_url + "/getUpdates"
sendmessage_url = token_url + "/sendMessage"

# Bechdel Test API urls
bechdel_url = "http://bechdeltest.com/api/v1/"
bechdel_url_imdb = bechdel_url + "getMovieByImdbId?imdbid="
bechdel_url_title = bechdel_url + "getMoviesByTitle?title="

# Messages content
start_text = "Hi!\nThis bot uses bechdeltest.com so you can easily know if a \
movie passes the Bechdel Test or not.\nIf you don't know what the Bechdel Test\
 is, type /about\n\n"

help_text = "List of available commands:\n/about Explains the Bechdel Test\n\
/help Shows this list of available commands\n/title Search movie by title\n\
/imdb Search movie by imdb unique id. You can get it using @iFilmBot\n\n\
Note that some non-English characters (e.g á, ü, ñ) don't work when \
searching by title. Use the imdb id instead."

about_text = "The Bechdel Test is a simple test to show the problem of \
gender inequality in movies.\n\nFor a movie to pass the test it has to \
satisfy the following criteria:\n1) It has to have at least two [named] women\
 in it.\n2) Who talk to each other.\n3) About something besides a man.\n\nThe \
simplicity of the criteria \"demonstrates how [...] women's complex and \
interesting lives are underrepresented or non existent in the film industry.\
\" as said by the author of the comic (Alison Bechdel) in which it appeared \
first.\n\nLearn more at http://bechdeltest.com and https://en.wikipedia.org/\
wiki/Bechdel_test"

error_unknown = "Unknown command\n"


def get_argument(message):
    message = message.split(" ")
    if "/title" in message:
        message.remove("/title")
    elif "/imdb" in message:
        message.remove("/imdb")
    elif "/title@BechdelBot" in message:
        message.remove("/title@BechdelBot")
    elif "/imdb@BechdelBot" in message:
        message.remove("/imdb@BechdelBot")

    # Bechdeltest.com API requires articles to be at the end
    if "the" in message:
        message[-1] = message[-1] + ","
        message.remove("the")
        message.append("the")

    argument = " ".join(message)
    return argument


def get_by_title(title):
    results = requests.get(bechdel_url_title + title)

    if results.status_code != 200:
        return "Server appears to have a problem. Try again later"
    results = json.loads(results.content)

    if len(results) > 5:
        for movie in results:
            if movie["title"] == "Ted":
                results = [movie]
        if len(results) != 1:
            return "Your search matches too many results. Try being more specific"
    elif len(results) == 0:
        return "No matches"

    output = []
    n = 1
    for movie in results:
        output.append("Result {0}:".format(n))
        output.append(" Title: {0}".format(movie["title"]))
        output.append(" Year: {0}".format(movie["year"]))

        if movie["rating"] == "0":
            passes = "No. There are not two [named] women"
        elif movie["rating"] == "1":
            passes = "No. Women don't talk to each other"
        elif movie["rating"] == "2":
            passes = "No. Women only talk about a man"
        elif movie["rating"] == "3":
            passes = "Yes!"

        output.append(" Passes the test? {0}".format(passes))
        output.append(" http://bechdeltest.com/view/{0}\n"
                      .format(movie["id"]))
        n += 1
    return "\n".join(output)


def get_by_imdb(imdb):
    results = requests.get(bechdel_url_imdb + imdb)

    if results.status_code != 200:
        return "Server appears to have a problem. Try again later"
    movie = json.loads(results.content)

    output = []
    n = 1
    output.append("Result No. {0}:".format(n))

    # If the imdb id isn't correct, server's response lacks some keys
    try:
        output.append(" Title: {0}".format(movie["title"]))
    except KeyError:
        return "No matches"
    output.append(" Year: {0}".format(movie["year"]))

    if movie["rating"] == "0":
        passes = "No. There are not two [named] women"
    elif movie["rating"] == "1":
        passes = "No. Women don't talk to each other"
    elif movie["rating"] == "2":
        passes = "No. Women only talk about a man"
    elif movie["rating"] == "3":
        passes = "Yes!"

    output.append(" Passes the test?: {0}".format(passes))
    output.append(" http://bechdeltest.com/view/{0}\n"
                  .format(movie["id"]))
    n += 1
    return "\n".join(output)


while True:
    # Load last update
    try:
        last_update_file = open("lastupdate")
        last_update = last_update_file.read().rstrip("\n")
        last_update_file.close()
    except:
        last_update = "0"  # If lastupdate file not present, read all updates

    getupdates_offset_url = getupdates_url + "?offset=" + str(int(last_update)
                                                              + 1)

    get_updates = requests.get(getupdates_offset_url)
    if get_updates.status_code != 200:
        print(get_updates.status_code)  # For debugging
        continue
    else:
        updates = json.loads(get_updates.content)["result"]

    for item in updates:
        if int(last_update) >= item["update_id"]:
            continue
        # Store last update
        last_update_file = open("lastupdate", "w")
        last_update_file.write(str(item["update_id"]))
        last_update_file.close()

        # Store time to log
        log = open("log", "a")
        log.write(str(time.time()) + "\n")
        log.close()

        # Group's status messages don't include "text" key
        try:
            text = item["message"]["text"]
        except KeyError:
            continue

        text = text.lower()

        if "/start" == text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + start_text + help_text)
        elif "/help" in text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + help_text)
        elif "/about" in text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + about_text)
        elif "/title" in text:
            argument = get_argument(text)
            if argument == "":
                result = "You need to specify the title"
            else:
                result = get_by_title(argument)
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + result)
        elif "/imdb" in text:
            argument = get_argument(text)
            if argument == "":
                result = "You need to specify the imdb id"
            else:
                result = get_by_imdb(argument)
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + result)
        elif item["message"]["chat"]["id"] < 0:
            # If it is none of the above and it's a group, let's guess it was
            # for another bot rather than sending the unknown command message
            continue
        else:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + error_unknown + help_text)
