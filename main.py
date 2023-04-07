from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap5
import numpy as np
from PIL import Image, ImageOps
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import RadioField, SubmitField
import os
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode
from io import BytesIO


app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI")
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
db = SQLAlchemy(app)


class ImageForm(FlaskForm):
    file = FileField("Select image", validators=[FileRequired(), FileAllowed(['jpg', 'png'], "Images only!")])
    code = RadioField("Select color code: ", choices=["Hex", "RGB"])
    submit = SubmitField("Submit")


class File(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    image = db.Column(db.LargeBinary)


with app.app_context():
    db.create_all()


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb


def give_most_color(file_path, code):
    my_image = Image.open(file_path).convert('RGB')
    size = my_image.size
    if size[0] >= 400 or size[1] >= 400:
        my_image = ImageOps.scale(image=my_image, factor=0.2)
    elif size[0] >= 600 or size[1] >= 600:
        my_image = ImageOps.scale(image=my_image, factor=0.4)
    elif size[0] >= 800 or size[1] >= 800:
        my_image = ImageOps.scale(image=my_image, factor=0.5)
    elif size[0] >= 1200 or size[1] >= 1200:
        my_image = ImageOps.scale(image=my_image, factor=0.6)
    my_image = ImageOps.posterize(my_image, 2)
    image_array = np.array(my_image)

    unique_colors = {}

    for column in image_array:
        for rgb in column:
            t_rgb = tuple(rgb)
            if t_rgb not in unique_colors:
                unique_colors[t_rgb] = 0
            if t_rgb in unique_colors:
                unique_colors[t_rgb] += 1

    sorted_unique_colors = sorted(
        unique_colors.items(), key=lambda x: x[1],
        reverse=True)
    converted_dict = dict(sorted_unique_colors)
    values = list(converted_dict.keys())
    colors_10 = values[0:12]

    if code == 'Hex':
        hex_list = []
        for key in colors_10:
            hex_code = rgb_to_hex(key)
            hex_list.append(hex_code)
        return hex_list
    else:
        return colors_10


@app.route('/', methods=['GET', 'POST'])
def home():
    form = ImageForm()
    if form.validate_on_submit():
        image = File()
        image.image = request.files['file'].read()
        image.name = request.files['file'].filename
        color_code = form.code.data
        db.session.add(image)
        db.session.commit()
        img_file = File.query.filter_by(name=image.name).first()
        image_f = BytesIO(img_file.image)
        mg = b64encode(img_file.image).decode("utf-8")
        colors = give_most_color(image_f, color_code)
        return render_template('index.html',
                               colors_list=colors,
                               code=color_code, form=form, image=image_f, file=mg)
    return render_template('index.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
