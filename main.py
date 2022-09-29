import gridfs
import imdb
from pathlib import Path
from pymongo import MongoClient
from flask import Flask, redirect, url_for, render_template, request, send_file
import requests
from config import KEY as myKey


app = Flask(__name__)
IMG_PATTERN = 'http://api.themoviedb.org/3/movie/{imdbid}/images?api_key={key}'
CONFIG_PATTERN = 'http://api.themoviedb.org/3/configuration?api_key={key}'
LOCAL_DOWNLOAD_DIR_NAME = "pics"
key = myKey

url = CONFIG_PATTERN.format(key=myKey)
r = requests.get(url)
config = r.json()


def mongo_conn():
    try:

        #conn = MongoClient(host='localhost', port=27017)
        conn = MongoClient(host='mongodb',port=27017)
        print("MongoDB connected", conn)
        return conn.postersDB

    except Exception as e:
        print("Error in mongo connection:", e)


# connects to database "posters"
db = mongo_conn()





def download_object(urls):
    """ save the images in a binary object named "contents" """
    for nr, url in enumerate(urls):
        if nr < 1:
            r = requests.get(url)
            contents = r.content
            break# access the response body as bytes, for non-text requests
    return contents








# #download_to_mongo("tt0371746")
# # first parameter is the download location including the name extension
# # second parameter is the file name to search in mongo
# def download_from_mongo(download_location, name):
#     data = db.fs.files.find_one({'filename': name})
#     my_id = data['_id']
#     fs = gridfs.GridFS(db)
#     outputdata = fs.get(my_id).read()
#     output = open(download_location, "wb")
#     output.write(outputdata)
#     output.close()
#     print("Download complete")
#
#
# #download_to_mongo('tt0070800')
# download_to_mongo('tt0070800')
# # download_to_mongo('tt2395427')
# # download_from_mongo("./pics/test.jpeg", "tt0371746")
# # download_from_mongo("./pics/test1.jpeg", "tt0070800")
# # download_from_mongo("./pics/test2.jpeg", "tt2395427")
#
# #new_list = ['tt0371746', 'tt0070800', 'tt0115218', 'tt1300854', 'tt1228705', 'tt0837143', 'tt0903135', 'tt1707807',
# #            'tt6218010', 'tt0120744', 'tt1233205', 'tt3296908', 'tt0096251', 'tt0206490']
#
# #for key in new_list:
# #    try:
# #        download_to_mongo(key)
# #        download_from_mongo(f'./pics/{key}.jpeg', key)
# #    except:
# #        print("this movie can't be downloaded for some reason")
#
# # testing ground

def _get_json(url):
    r = requests.get(url)
    return r.json()


def get_poster_urls(imdbid):
    """ return a list of  url web addresses for posters of a given IMDB id
         all  the returned  links from 'themoviedb.org'.
        has a maximum image size.

        Args:
            imdbid (str): IMDB id of the movie
        Returns:
            list: list of urls to the images
    """
    config = _get_json(CONFIG_PATTERN.format(key=myKey))
    base_url = config['images']['base_url'] # http://image.tmdb.org/t/p/
    sizes = config['images']['poster_sizes']#  ["w92","w154","w185","w342","w500","w780","original"]

    def size_str_to_int(x):
        """
                'sizes' should be sorted in ascending order, so
                max_size = sizes[-1]
                should get the largest size as well.
                return infinity if x = original, else slice the intger part from "w92", or "w154"
                 Args:
                    list(str): IMDB id of the movie
                Returns:
                    float: maximum avliable size in list
            """

        return float("inf") if x == 'original' else int(x[1:])


    max_size = max(sizes, key=size_str_to_int) #lambda is an anonymous function

    posters = _get_json(IMG_PATTERN.format(key=myKey, imdbid=imdbid))["posters"]
    # for i in posters_list:
    #     print(i['file_path'])
    poster_urls = []
    for poster in posters:
        real_path = poster['file_path']
        url = "{0}{1}{2}".format(base_url, max_size, real_path)
        poster_urls.append(url)
       # print(url)
    print(len(url))
    return poster_urls



# download image from imdb straight into mongo
# takes movie_id as 'str' e.g: 'tt4154796'
def download_to_mongo(movie_id, count=None,):
    urls = get_poster_urls(movie_id)
    if count is not None:
        urls = urls[:count]
    data = download_object(urls)
    fs = gridfs.GridFS(db)
    fs.put(data, filename=movie_id)
    print("upload complete")


def download_from_mongo(download_location, name):
    data = db.fs.files.find_one({'filename': name})
    my_id = data['_id']
    fs = gridfs.GridFS(db)
    outputdata = fs.get(my_id).read()
    output = open(download_location, "wb")
    output.write(outputdata)
    output.close()
    print("Download complete")



#download_to_mongo("tt0120744",2)
#download_from_mongo("./pics/test.jpeg", "tt4154796")


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/', methods=["POST"])
def search():
    # movie name
    global movie
    movie = request.form['movie']
    ## hostname = "google.com"  # example
    ## response = os.system("ping -c 1 " + hostname)
    return redirect(url_for("results"))


# show the images and results of the search method
@app.route('/search', methods=["GET", "POST"])
def results():
    ia = imdb.IMDb()
    movies_list = ia.search_movie(movie)
    global movie_id
    # my list has the conditions of movies, if true the file exists.
    my_list = []
    movies_id_list = []
    for movie_match in movies_list:
        movies_id_list.append('tt' + movie_match.movieID)

    for movie_id in movies_id_list:
        try:
            if db.fs.files.count_documents({'filename': movie_id}):
                ## print("db1")
                continue
            else:
                ## print("db2")
                download_to_mongo(movie_id)
        except Exception as e:
            print("exception", e)
            continue
    """ This block is extremely important, it makes a list of the possible posters to download"""
    for movie_id in movies_id_list:
        try:
            data = db.fs.files.find_one({'filename': movie_id})
            my_id = data['_id']
            fs = gridfs.GridFS(db)
            my_poster = (fs.get(my_id).read())
            my_poster = len(my_poster)
            if db.fs.files.count_documents({'filename': movie_id}) and my_poster:
                my_list.append(True)
                continue
            else:
                my_list.append(False)
        except:
            my_list.append(False)

    my_zip = list(zip(movies_list, my_list))
    return render_template("search.html", content=my_zip)


@app.route('/search/download', methods=["GET", "POST"])
def download():

    # create the directory if it does not exist
    Path(f"./{LOCAL_DOWNLOAD_DIR_NAME}").mkdir(exist_ok=True)

    # receive Movie ID list
    movie_id_list = request.form.getlist('movieID')
    # downloads all the chosen posters to local machine
    for movie_id in movie_id_list:
        try:
            download_from_mongo(f"./{LOCAL_DOWNLOAD_DIR_NAME}/{movie_id}" + '.jpeg', movie_id)
            path = f'./pics/{movie_id}' + '.jpeg'
            return send_file(path, as_attachment=True)
        except:
            continue
    return render_template("download.html")


@app.route('/posters/<name>')
def show_poster(name):
    data = db.fs.files.find_one({'filename': name})
    my_id = data['_id']
    fs = gridfs.GridFS(db)
    my_poster = fs.get(my_id).read()
    # response.content = 'image/jpeg'
    return my_poster


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051)
