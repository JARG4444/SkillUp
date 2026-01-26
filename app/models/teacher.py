from ..extensions import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    exp = db.Column(db.String(50))
    subject = db.Column(db.String(50))
    bio = db.Column(db.String(350))
    photo = db.Column(db.String(300))

    def __repr__(self):
        return f'<Teacher {self.name}>'
