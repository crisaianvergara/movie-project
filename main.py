from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
# Create database movie db
app.app_context().push()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
# Bootstrap
Bootstrap(app)

# Movie Api Key and Endpoint
MOVIE_DB_API_KEY = "415d2c68ce92d4ab116843c944dda2bf"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3"
MOVIE_DB_IMG_URL = "https://image.tmdb.org/t/p/w500"

# Create Movie table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class EditForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    all_movies = Movie.query.order_by(asc("rating"))
    ranking = all_movies.count()
    for movie in all_movies:
        movie.ranking = ranking
        db.session.commit()
        ranking -= 1
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = EditForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)
    if edit_form.validate_on_submit():
        movie_to_update.rating = float(edit_form.rating.data)
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=edit_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        params = {
            "api_key": MOVIE_DB_API_KEY,
            "query": add_form.title.data,
        }
        response = requests.get(f"{MOVIE_DB_SEARCH_URL}/search/movie", params=params)
        response.raise_for_status()
        data_movies = response.json()["results"]
        return render_template("select.html", data=data_movies)
    return render_template("add.html", form=add_form)


@app.route("/add-movie")
def add_movie():
    movie_id = request.args.get("id")
    params = {"api_key": MOVIE_DB_API_KEY}
    response = requests.get(f"{MOVIE_DB_SEARCH_URL}/movie/{movie_id}", params=params)
    response.raise_for_status()
    data_movie = response.json()
    new_movie = Movie(
        title=data_movie["title"],
        year=data_movie["release_date"].split("-")[0],
        description=data_movie["overview"],
        img_url=f"{MOVIE_DB_IMG_URL}{data_movie['poster_path']}",
    )
    db.session.add(new_movie)
    db.session.commit()
    movie_to_rate = Movie.query.filter_by(title=data_movie["title"]).first()
    return redirect(url_for("edit", id=movie_to_rate.id))


if __name__ == "__main__":
    app.run(debug=True)
